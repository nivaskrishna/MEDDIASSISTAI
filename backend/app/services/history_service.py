"""
History Service — Chat History & Saved Diagnoses
Stores analysis results in MongoDB Atlas (free tier).
Degrades gracefully to no-op when MONGODB_URI is not configured.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


async def save_analysis(
    session_id: str,
    query: str,
    condition: str,
    severity: str,
    first_aid: str,
    doctor_type: str,
    symptoms: List[str],
) -> bool:
    """
    Persist one analysis result to the chat_history collection.
    Returns True on success, False if MongoDB is unavailable.
    """
    from app.db.mongo import get_collection
    col = get_collection("chat_history")
    if col is None:
        return False  # MongoDB not configured

    doc = {
        "session_id": session_id,
        "query":      query,
        "condition":  condition,
        "severity":   severity,
        "first_aid":  first_aid,
        "doctor_type": doctor_type,
        "symptoms":   symptoms,
        "created_at": _utcnow(),
    }
    try:
        await col.insert_one(doc)
        logger.info("[history] Saved analysis for session %s — condition: %s", session_id, condition)
        return True
    except Exception as exc:
        logger.warning("[history] Failed to save analysis: %s", exc)
        return False


async def get_history(session_id: str, limit: int = 20) -> List[dict]:
    """
    Retrieve recent analyses for a browser session (newest first).
    Returns an empty list if MongoDB is unavailable.
    """
    from app.db.mongo import get_collection
    col = get_collection("chat_history")
    if col is None:
        return []

    try:
        cursor = col.find(
            {"session_id": session_id},
            {"_id": 0},  # Exclude the MongoDB ObjectId from results
            sort=[("created_at", -1)],
            limit=limit,
        )
        docs = await cursor.to_list(length=limit)
        # Convert datetime objects to ISO strings for JSON serialisation
        for d in docs:
            if isinstance(d.get("created_at"), datetime):
                d["created_at"] = d["created_at"].isoformat()
        return docs
    except Exception as exc:
        logger.warning("[history] Failed to fetch history: %s", exc)
        return []


async def delete_history(session_id: str) -> int:
    """
    Delete all history entries for a session.
    Returns the number of deleted documents.
    """
    from app.db.mongo import get_collection
    col = get_collection("chat_history")
    if col is None:
        return 0

    try:
        result = await col.delete_many({"session_id": session_id})
        logger.info("[history] Deleted %d entries for session %s", result.deleted_count, session_id)
        return result.deleted_count
    except Exception as exc:
        logger.warning("[history] Failed to delete history: %s", exc)
        return 0


async def save_diagnosis(
    session_id: str,
    condition: str,
    severity: str,
    first_aid: str,
    doctor_type: str,
) -> bool:
    """
    Save a user-bookmarked diagnosis to saved_diagnoses collection.
    """
    from app.db.mongo import get_collection
    col = get_collection("saved_diagnoses")
    if col is None:
        return False

    doc = {
        "session_id": session_id,
        "condition":  condition,
        "severity":   severity,
        "first_aid":  first_aid,
        "doctor_type": doctor_type,
        "saved_at":   _utcnow(),
    }
    try:
        await col.insert_one(doc)
        logger.info("[history] Saved diagnosis '%s' for session %s", condition, session_id)
        return True
    except Exception as exc:
        logger.warning("[history] Failed to save diagnosis: %s", exc)
        return False


async def get_saved_diagnoses(session_id: str) -> List[dict]:
    """Return all saved (bookmarked) diagnoses for a session."""
    from app.db.mongo import get_collection
    col = get_collection("saved_diagnoses")
    if col is None:
        return []

    try:
        cursor = col.find(
            {"session_id": session_id},
            {"_id": 0},
            sort=[("saved_at", -1)],
        )
        docs = await cursor.to_list(length=50)
        for d in docs:
            if isinstance(d.get("saved_at"), datetime):
                d["saved_at"] = d["saved_at"].isoformat()
        return docs
    except Exception as exc:
        logger.warning("[history] Failed to fetch saved diagnoses: %s", exc)
        return []
