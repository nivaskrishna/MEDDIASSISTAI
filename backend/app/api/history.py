"""
History API Router — Chat History & Saved Diagnoses
POST /api/history/save            → save an analysis result
GET  /api/history/{session_id}    → get recent analyses
DELETE /api/history/{session_id}  → clear history
POST /api/history/save-diagnosis  → bookmark a diagnosis
GET  /api/history/{session_id}/saved → get bookmarked diagnoses
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
from app.services.history_service import (
    save_analysis,
    get_history,
    delete_history,
    save_diagnosis,
    get_saved_diagnoses,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class SaveAnalysisRequest(BaseModel):
    session_id: str
    query: str
    condition: str
    severity: str
    first_aid: str
    doctor_type: str
    symptoms: List[str] = []


class SaveDiagnosisRequest(BaseModel):
    session_id: str
    condition: str
    severity: str
    first_aid: str
    doctor_type: str


@router.post("/save")
async def save_analysis_endpoint(req: SaveAnalysisRequest):
    """Save an analysis result to MongoDB history."""
    ok = await save_analysis(
        session_id=req.session_id,
        query=req.query,
        condition=req.condition,
        severity=req.severity,
        first_aid=req.first_aid,
        doctor_type=req.doctor_type,
        symptoms=req.symptoms,
    )
    if not ok:
        # Not an error — MongoDB might just not be configured
        return {"saved": False, "message": "MongoDB not configured or unavailable"}
    return {"saved": True}


@router.get("/{session_id}")
async def get_history_endpoint(session_id: str, limit: int = 20):
    """Get recent analysis history for a browser session."""
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="Invalid session_id")
    data = await get_history(session_id, limit=limit)
    return {"session_id": session_id, "count": len(data), "history": data}


@router.delete("/{session_id}")
async def delete_history_endpoint(session_id: str):
    """Clear all history for a browser session."""
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="Invalid session_id")
    deleted = await delete_history(session_id)
    return {"deleted": deleted}


@router.post("/save-diagnosis")
async def save_diagnosis_endpoint(req: SaveDiagnosisRequest):
    """Bookmark a diagnosis for a browser session."""
    ok = await save_diagnosis(
        session_id=req.session_id,
        condition=req.condition,
        severity=req.severity,
        first_aid=req.first_aid,
        doctor_type=req.doctor_type,
    )
    return {"saved": ok}


@router.get("/{session_id}/saved")
async def get_saved_endpoint(session_id: str):
    """Get all bookmarked diagnoses for a session."""
    data = await get_saved_diagnoses(session_id)
    return {"session_id": session_id, "count": len(data), "saved": data}
