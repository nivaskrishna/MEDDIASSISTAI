"""
SDXL Image Generation API Router

POST /api/image-gen/generate
    Body:  { "prompt": "<text>" }
    Returns: { "image_url": "data:image/jpeg;base64,…", "prompt_used": "…" }
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from app.services.sdxl_service import generate_sdxl_image, _build_prompt

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ImageGenRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Text prompt for image generation")


class ImageGenResponse(BaseModel):
    image_url: str    # data-URI: data:image/jpeg;base64,…
    prompt_used: str  # full prompt sent to the model (includes quality modifiers)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=ImageGenResponse)
async def generate_image(request: ImageGenRequest):
    """
    Generate an image with Stable Diffusion XL.

    The backend:
    1. Appends quality modifiers to the prompt.
    2. Checks a local disk cache (avoids duplicate generation).
    3. Tries HuggingFace Inference API (if key present).
    4. Falls back to Pollinations.ai SDXL (always available, no key needed).

    Returns a base64 data-URI in `image_url` ready for <img src>.
    """
    prompt_used = _build_prompt(request.prompt)
    logger.info("[image-gen] POST /generate | raw prompt: %.80s…", request.prompt)
    logger.info("[image-gen] Full prompt with quality suffix: %.120s…", prompt_used)

    try:
        data_uri = await generate_sdxl_image(request.prompt)
        logger.info("[image-gen] SUCCESS | data-URI length: %d chars", len(data_uri))

        return ImageGenResponse(
            image_url=data_uri,
            prompt_used=prompt_used,
        )

    except RuntimeError as exc:
        logger.error("[image-gen] Generation failed (RuntimeError): %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Image generation failed: {exc}",
        )
    except Exception as exc:
        logger.exception("[image-gen] Unexpected error during generation")
        raise HTTPException(
            status_code=500,
            detail="Image generation failed unexpectedly. Check server logs.",
        )
