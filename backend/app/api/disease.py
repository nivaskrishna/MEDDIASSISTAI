"""
Disease Stats API Router
GET /api/disease/stats           → global COVID totals
GET /api/disease/country/{code}  → per-country stats
"""
from fastapi import APIRouter, HTTPException
import logging
from app.services.disease_service import get_global_stats, get_country_stats

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def global_stats():
    """Return worldwide disease/COVID summary stats."""
    data = await get_global_stats()
    if not data:
        raise HTTPException(status_code=502, detail="Could not fetch disease statistics")
    return data


@router.get("/country/{country_code}")
async def country_stats(country_code: str):
    """Return disease stats for a specific country (ISO2/ISO3 or name)."""
    data = await get_country_stats(country_code)
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for '{country_code}'")
    return data
