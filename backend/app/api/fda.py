"""
OpenFDA Drug Info API Router
GET /api/fda/drug?name=paracetamol   → list of matching drug records
"""
from fastapi import APIRouter, HTTPException, Query
import logging
from app.services.fda_service import search_drug

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/drug")
async def drug_search(
    name: str = Query(..., min_length=2, description="Drug brand or generic name"),
    limit: int = Query(5, ge=1, le=10, description="Max results"),
):
    """
    Search FDA drug labels by brand or generic name.
    Returns indications, dosage, side effects, warnings.
    """
    logger.info("[fda-api] Drug search: %s (limit=%d)", name, limit)
    results = await search_drug(name, limit=limit)
    if results is None:
        raise HTTPException(status_code=502, detail="OpenFDA API error")
    return {"query": name, "count": len(results), "results": results}
