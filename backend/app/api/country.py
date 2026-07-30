"""
Country Info API Router
GET /api/country/{iso2}          → country metadata + emergency numbers
GET /api/country/{iso2}/emergency → just emergency numbers
"""
from fastapi import APIRouter, HTTPException
import logging
from app.services.country_service import get_country_info, get_emergency_numbers

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{iso2}")
async def country_info(iso2: str):
    """Return country metadata and emergency phone numbers by ISO2 code."""
    if len(iso2) != 2:
        raise HTTPException(status_code=400, detail="Provide a valid 2-letter ISO country code (e.g. 'IN', 'US')")
    data = await get_country_info(iso2)
    if not data:
        raise HTTPException(status_code=404, detail=f"Country '{iso2}' not found")
    return data


@router.get("/{iso2}/emergency")
async def emergency_numbers(iso2: str):
    """Return only the emergency phone numbers for the given country code."""
    if len(iso2) != 2:
        raise HTTPException(status_code=400, detail="Provide a valid 2-letter ISO country code")
    return await get_emergency_numbers(iso2)
