"""
SDXL Image Generation Service
Uses Pollinations.ai (https://image.pollinations.ai) as the primary backend
since it requires no API key and is confirmed reachable from this machine.

If HUGGINGFACE_API_KEY is set the service attempts HuggingFace Inference API
first, with automatic fallback to Pollinations.ai on any failure.
"""

import httpx
import base64
import hashlib
import json
import logging
import urllib.parse
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# Pollinations.ai – free, no key required, confirmed reachable.
_POLLINATIONS_SDXL = (
    "https://image.pollinations.ai/prompt/{prompt}"
    "?width=768&height=768&nologo=true&model=turbo&seed={seed}"
)

# HuggingFace Inference API (used only when HUGGINGFACE_API_KEY is set).
_HF_SDXL_URL = (
    "https://api-inference.huggingface.co/models/"
    "stabilityai/stable-diffusion-xl-base-1.0"
)

# Quality modifiers appended to every user prompt.
_QUALITY_SUFFIX = (
    "high quality, highly detailed, professional digital art, "
    "sharp focus, cinematic lighting"
)

# Disk cache to avoid re-generating identical prompts.
import os as _os
if _os.environ.get("VERCEL"):
    _CACHE_DIR = Path("/tmp/image_cache")
else:
    _CACHE_DIR = Path("app/data/image_cache")
try:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    _CACHE_DIR = Path("/tmp/image_cache")
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_prompt(user_prompt: str) -> str:
    """Append quality modifiers to the raw user prompt."""
    prompt = user_prompt.strip().rstrip(",")
    return f"{prompt}, {_QUALITY_SUFFIX}"


def _detect_mime(image_bytes: bytes) -> str:
    """Sniff the MIME type from magic bytes."""
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"  # default


def _to_data_uri(image_bytes: bytes) -> str:
    mime = _detect_mime(image_bytes)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# HuggingFace backend
# ---------------------------------------------------------------------------

async def _generate_via_huggingface(final_prompt: str) -> bytes:
    """
    Call HuggingFace Inference API.

    Error handling:
        401 – invalid API key
        403 – access denied (model gated / plan restriction)
        429 – rate limit exceeded
        503 – model loading (wait_for_model=True should handle this, but guard anyway)
    Raises RuntimeError on any failure so the caller can fall back.
    """
    api_key = settings.HUGGINGFACE_API_KEY
    if not api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY is not set")

    logger.info("[HF] Sending request to SDXL | prompt: %.80s…", final_prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": final_prompt,
        "parameters": {"num_inference_steps": 30, "guidance_scale": 7.5},
        "options": {"wait_for_model": True},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(_HF_SDXL_URL, json=payload, headers=headers)
    except httpx.ConnectError as exc:
        raise RuntimeError(f"HuggingFace DNS/connection error: {exc}") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"HuggingFace request timed out: {exc}") from exc

    logger.info("[HF] Response status: %d | content-type: %s | bytes: %d",
                response.status_code,
                response.headers.get("content-type", "unknown"),
                len(response.content))

    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            logger.info("[HF] Image generated successfully | %d bytes", len(response.content))
            return response.content
        # HF sometimes returns JSON even on 200 when the model is loading
        try:
            body = response.json()
            logger.warning("[HF] 200 but non-image JSON body: %s", str(body)[:200])
            if "estimated_time" in body:
                raise RuntimeError(
                    f"HuggingFace model is loading (estimated {body['estimated_time']:.0f}s)"
                )
        except (json.JSONDecodeError, ValueError):
            pass
        raise RuntimeError(
            f"HuggingFace 200 but unexpected content-type: {content_type}"
        )

    # Structured error responses
    error_body = response.text[:300]
    if response.status_code == 401:
        raise RuntimeError(f"HuggingFace: invalid API key (401) — {error_body}")
    if response.status_code == 403:
        raise RuntimeError(f"HuggingFace: access denied (403) — {error_body}")
    if response.status_code == 429:
        raise RuntimeError(f"HuggingFace: rate limit exceeded (429) — {error_body}")
    if response.status_code == 503:
        # Model still loading even with wait_for_model=True
        raise RuntimeError(f"HuggingFace: model unavailable (503) — {error_body}")

    raise RuntimeError(
        f"HuggingFace API error {response.status_code}: {error_body}"
    )


# ---------------------------------------------------------------------------
# Pollinations.ai backend  (primary / fallback)
# ---------------------------------------------------------------------------

async def _generate_via_pollinations(final_prompt: str, seed: int = 42) -> bytes:
    """
    Call Pollinations.ai SDXL (turbo model).

    Retries up to 5 times with exponential back-off.
    On 429 (rate limit) waits before retrying.
    Raises RuntimeError after all attempts fail.
    """
    import asyncio

    encoded = urllib.parse.quote(final_prompt)
    url = _POLLINATIONS_SDXL.format(prompt=encoded, seed=seed)

    logger.info("[Pollinations] Requesting image | seed=%d | url: %.100s…", seed, url)

    max_attempts = 5
    base_delay = 2.0  # seconds

    async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.get(url)
                logger.info(
                    "[Pollinations] Attempt %d → status %d | content-type: %s | bytes: %d",
                    attempt,
                    response.status_code,
                    response.headers.get("content-type", "unknown"),
                    len(response.content),
                )

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        return response.content
                    logger.warning(
                        "[Pollinations] 200 but non-image content-type: %s", content_type
                    )

                elif response.status_code == 429:
                    delay = base_delay * (2 ** (attempt - 1))  # 2, 4, 8, 16, 32s
                    logger.warning(
                        "[Pollinations] 429 Rate Limited on attempt %d — waiting %.0fs before retry",
                        attempt, delay,
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(delay)
                    continue

                else:
                    logger.warning(
                        "[Pollinations] Attempt %d non-200 status: %d — %s",
                        attempt, response.status_code, response.text[:100],
                    )

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.warning("[Pollinations] Attempt %d network error: %s", attempt, exc)
            except Exception as exc:
                logger.exception("[Pollinations] Attempt %d unexpected error", attempt)

    raise RuntimeError(f"Pollinations.ai SDXL failed after {max_attempts} attempts")



# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

async def generate_sdxl_image(prompt: str) -> str:
    """
    Generate an image with SDXL and return a data-URI.

    Strategy:
      1. Check disk cache (MD5 hash of final prompt).
      2. Try HuggingFace Inference API if HUGGINGFACE_API_KEY is set.
      3. Fall back to Pollinations.ai (always attempted if HF fails or key absent).

    Returns:
        ``data:image/jpeg;base64,<b64>`` string ready for <img src>.
    """
    final_prompt = _build_prompt(prompt)
    seed = int(hashlib.md5(final_prompt.encode()).hexdigest(), 16) % 100_000
    cache_key = hashlib.md5(final_prompt.encode()).hexdigest()
    cache_path = _CACHE_DIR / f"sdxl_{cache_key}.jpg"

    logger.info(
        "=== SDXL generation START | seed=%d | cache_key=%s | prompt: %.80s…",
        seed, cache_key, final_prompt,
    )

    # 1. Cache hit
    if cache_path.exists():
        image_bytes = cache_path.read_bytes()
        logger.info("=== SDXL cache HIT | %d bytes | key=%s", len(image_bytes), cache_key)
        return _to_data_uri(image_bytes)

    # 2. HuggingFace (if key present)
    image_bytes = None
    if settings.HUGGINGFACE_API_KEY:
        try:
            image_bytes = await _generate_via_huggingface(final_prompt)
            logger.info("=== SDXL via HuggingFace OK | %d bytes", len(image_bytes))
        except Exception as exc:
            logger.warning(
                "=== SDXL HuggingFace FAILED (%s) → falling back to Pollinations", exc
            )

    # 3. Pollinations.ai fallback
    if image_bytes is None:
        image_bytes = await _generate_via_pollinations(final_prompt, seed=seed)
        logger.info("=== SDXL via Pollinations OK | %d bytes", len(image_bytes))

    # Persist to cache
    cache_path.write_bytes(image_bytes)
    logger.info("=== SDXL generation COMPLETE | cached at %s", cache_path)

    return _to_data_uri(image_bytes)
