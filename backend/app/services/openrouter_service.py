"""
OpenRouter AI Service — Free Model Fallback
Used when Gemini API is unavailable, rate-limited, or returns an error.

Free models (no cost, just need an account):
  - deepseek/deepseek-r1-0528:free  (best reasoning, recommended)
  - mistralai/mistral-7b-instruct:free
  - meta-llama/llama-3-8b-instruct:free

Get a free API key at: https://openrouter.ai/keys
"""
import httpx
import json
import logging
import re
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
# Free models — verified working against your OpenRouter account (2026-06-18)
# Tested in priority order; all are :free and respond correctly
_MODEL         = "nvidia/nemotron-3-ultra-550b-a55b:free"  # Primary   — verified ✅
_FALLBACK_MODEL = "openai/gpt-oss-20b:free"               # Fallback 1 — verified ✅
_FALLBACK2     = "meta-llama/llama-3.3-70b-instruct:free" # Fallback 2 — works when not rate-limited

# Same system prompt as gemini_service.py — keeps output format consistent
SYSTEM_PROMPT = """
You are MediAssist AI, an expert medical assistant. Analyze the user's symptoms.
Return ONLY a valid JSON object with NO markdown, NO code blocks, just raw JSON.
The JSON must have these exact keys:
- "condition": short string for possible condition
- "first_aid": detailed step-by-step first aid instructions
- "severity": one of "Low", "Medium", "High", "Critical"
- "doctor_type": recommended doctor specialty
- "image_prompt": specific medical illustration description for first aid
- "symptoms": list of key symptom strings
"""


def _extract_json(text: str) -> dict:
    """Extract JSON from model output, stripping any markdown fences."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Strip markdown code fences
    clean = re.sub(r"```(?:json)?", "", text).strip().strip("`")
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    # Find first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    logger.warning("[OpenRouter] Could not parse JSON from response: %.200s", text)
    return {}


async def _call_openrouter(messages: list, model: str) -> dict:
    """Make a single call to the OpenRouter API."""
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://mediassist.ai",   # Required by OpenRouter
        "X-Title": "MediAssist AI",                 # Shows in usage dashboard
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.3,
    }

    logger.info("[OpenRouter] Calling model: %s", model)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(_BASE_URL, json=payload, headers=headers)

    logger.info("[OpenRouter] Response status: %d", r.status_code)

    if r.status_code == 429:
        raise RuntimeError("OpenRouter rate limit exceeded for free tier")
    if r.status_code == 401:
        raise RuntimeError("OpenRouter: invalid API key (401)")
    if r.status_code == 402:
        raise RuntimeError("OpenRouter: free tier credits exhausted (402)")
    r.raise_for_status()

    body = r.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    logger.info("[OpenRouter] Raw content (first 200): %.200s", content)
    return _extract_json(content)


async def analyze_with_openrouter(query: str, image_b64: Optional[str] = None) -> dict:
    """
    Analyze symptoms using a free OpenRouter model.
    Returns same JSON structure as gemini_service.analyze_symptoms().

    Falls back to a secondary free model if the primary fails.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.warning("[OpenRouter] No API key — skipping OpenRouter fallback")
        return {}

    # Build messages — no image support for text-only free models
    user_content = query
    if image_b64:
        user_content += "\n[Note: An image was provided but cannot be analyzed by the fallback model. Please describe visible symptoms in text.]"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user",   "content": user_content},
    ]

    # Try primary model
    try:
        result = await _call_openrouter(messages, _MODEL)
        if result.get("condition"):
            logger.info("[OpenRouter] Primary model succeeded: %s", _MODEL)
            return result
    except Exception as exc:
        logger.warning("[OpenRouter] Primary model %s failed: %s", _MODEL, exc)

    # Try first fallback model
    try:
        result = await _call_openrouter(messages, _FALLBACK_MODEL)
        if result.get("condition"):
            logger.info("[OpenRouter] Fallback model succeeded: %s", _FALLBACK_MODEL)
            return result
    except Exception as exc:
        logger.warning("[OpenRouter] Fallback model %s failed: %s", _FALLBACK_MODEL, exc)

    # Try second fallback model
    try:
        result = await _call_openrouter(messages, _FALLBACK2)
        if result.get("condition"):
            logger.info("[OpenRouter] Second fallback model succeeded: %s", _FALLBACK2)
            return result
    except Exception as exc:
        logger.error("[OpenRouter] All models failed. Last error: %s", exc)

    return {}
