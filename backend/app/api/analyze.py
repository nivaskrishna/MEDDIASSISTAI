from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from fastapi.responses import RedirectResponse
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, StepImageItem
from app.services.gemini_service import analyze_symptoms
from app.services.image_generation_service import get_flux_image_for_step, generate_step_prompt
from typing import Optional
import logging
import re
import urllib.parse
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()

def parse_first_aid_steps_to_list(first_aid_text: str) -> list[str]:
    """Helper to parse first aid instructions into clean step-by-step items, matching the client-side parsing logic."""
    if not first_aid_text:
        return []
    
    # 1. Split lines and filter out any warning/note/disclaimer indicators
    raw_lines = [line.strip() for line in first_aid_text.split('\n') if line.strip()]
    main_lines = []
    
    for line in raw_lines:
        if any(line.startswith(x) for x in ['⚠️', '⚡', '🚨']) or \
           any(line.lower().startswith(x) for x in ['note:', 'warning:', 'disclaimer:']):
            continue
        main_lines.append(line)
        
    main_text = "\n".join(main_lines)
    
    # 2. Check if there are numbered parts anywhere (inline or on newlines)
    parts = re.split(r'(?=\b\d{1,2}[\.\)](?!\d))', main_text)
    parts = [p.strip() for p in parts if p.strip()]
    
    has_numbered_parts = any(re.match(r'^\d{1,2}[\.\)]', part) for part in parts)
    
    steps = []
    if has_numbered_parts:
        for part in parts:
            match = re.match(r'^(\d{1,2})[\.\)]\s*(.*)', part, re.DOTALL)
            if match:
                steps.append(match.group(2).strip())
            else:
                if steps:
                    steps[-1] += "\n" + part
                else:
                    steps.append(part)
    else:
        # Split by sentence boundaries using lookbehind for punctuation
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', main_text) if s.strip()]
        steps = sentences if sentences else [main_text]
        
    # 3. Clean any step numbering/bullet prefixes and filter out short steps
    cleaned_steps = []
    for s in steps:
        s_clean = re.sub(r'^\d{1,2}[\.\)]\s*', '', s).strip()
        s_clean = re.sub(r'^[\-\*]\s*', '', s_clean).strip()
        s_clean = re.sub(r'\s+', ' ', s_clean)
        if s_clean and len(s_clean) > 4:
            cleaned_steps.append(s_clean)
            
    return cleaned_steps

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
):
    if not request.query and not request.image:
        raise HTTPException(status_code=400, detail="Query or Image cannot be empty")

    # 1. Symptom analysis
    result = await analyze_symptoms(request.query, request.image)
    condition = result.get("condition", "Unknown")
    first_aid = result.get("first_aid", "Not available")

    # 2. Extract first aid steps
    steps = parse_first_aid_steps_to_list(first_aid)

    # 3. Build step items WITHOUT pre-generating images.
    #    The frontend InlineStepCard component fetches images lazily per step,
    #    so pre-generating here just blocks the response for 20-30s unnecessarily.
    step_images = [
        StepImageItem(
            step_number=idx + 1,
            step_text=step_text,
            search_query=generate_step_prompt(condition, step_text),
            image_url=None   # Frontend will generate via /api/image-gen/generate
        )
        for idx, step_text in enumerate(steps)
    ]

    # 5. Fire-and-forget: save to MongoDB history (non-blocking, won't delay response)
    if x_session_id:
        try:
            from app.services.history_service import save_analysis as _save
            background_tasks.add_task(
                _save,
                session_id=x_session_id,
                query=request.query or "[image analysis]",
                condition=condition,
                severity=result.get("severity", "Unknown"),
                first_aid=first_aid,
                doctor_type=result.get("doctor_type", "General Physician"),
                symptoms=result.get("symptoms", []),
            )
        except Exception as hist_err:
            logger.debug("History save skipped: %s", hist_err)

    return AnalyzeResponse(
        condition=condition,
        first_aid=first_aid,
        severity=result.get("severity", "Unknown"),
        doctor_type=result.get("doctor_type", "General Physician"),
        image_prompt=result.get("image_prompt"),
        symptoms=result.get("symptoms", []),
        step_images=step_images
    )

@router.post("/search-images", response_model=AnalyzeResponse)
async def search_images_endpoint(request: AnalyzeRequest):
    """Workflow: User Symptoms -> Analysis -> Extract Steps -> Search Openverse/Wikimedia -> Return Image URLs"""
    return await analyze(request)

@router.get("/step-image")
async def get_step_image(condition: str = None, step_text: str = None, prompt: str = None):
    """GET endpoint to support backward compatibility. Redirects directly to the generated image URL."""
    if not condition and not step_text and not prompt:
        raise HTTPException(status_code=400, detail="Parameters condition and step_text or prompt are required")
    
    # Search for a single unique image using the workflow client
    url = await get_flux_image_for_step(condition or "General", step_text or prompt or "first aid", 1)
    if url:
        return RedirectResponse(url=url, status_code=307)
        
    raise HTTPException(status_code=500, detail="Step image generation yielded no results")

from fastapi.responses import FileResponse

@router.get("/image-file/{image_hash}")
async def get_cached_image(image_hash: str):
    from app.services.image_generation_service import CACHE_DIR
    import os
    file_path = CACHE_DIR / f"{image_hash}.jpg"
    if file_path.exists():
        return FileResponse(file_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")

@router.get("/step-image-fallback")
async def step_image_fallback(condition: str = None, step_num: int = None):
    # Safe reliable fallback image that doesn't block hotlinking
    return RedirectResponse(url="https://placehold.co/600x400/0f172a/3b82f6?text=Generating+Image...\\nRetrying...", status_code=307)

