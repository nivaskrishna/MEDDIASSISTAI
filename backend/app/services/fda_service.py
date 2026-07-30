"""
OpenFDA Drug Information Service
Fetches FDA-approved drug label data from the free OpenFDA API.
https://open.fda.gov/apis/drug/label/

Free limits:
  - No key:  1,000 requests / day  (per IP)
  - With key: 120,000 requests / day
"""
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://api.fda.gov/drug/label.json"


def _fda_params(extra: dict) -> dict:
    params = dict(extra)
    if getattr(settings, "OPENFDA_API_KEY", ""):
        params["api_key"] = settings.OPENFDA_API_KEY
    return params


def _safe(data: dict, *keys, default="Not available") -> str:
    """Safely extract the first element of a nested list field."""
    val = data
    for k in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(k)
        if val is None:
            return default
    if isinstance(val, list):
        return val[0] if val else default
    return str(val) if val else default


async def search_drug(name: str, limit: int = 5) -> list[dict]:
    """
    Search OpenFDA for drugs matching `name`.
    Returns a list of simplified drug info dicts.
    """
    if not name or len(name.strip()) < 2:
        return []

    query = f'(openfda.brand_name:"{name}" OR openfda.generic_name:"{name}")'
    params = _fda_params({"search": query, "limit": limit})

    logger.info("[OpenFDA] Searching for drug: %s", name)
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(_BASE, params=params)

        if r.status_code == 404:
            logger.info("[OpenFDA] No results for: %s", name)
            return []
        if r.status_code == 429:
            logger.warning("[OpenFDA] Rate limit hit")
            return []

        r.raise_for_status()
        results = r.json().get("results", [])
        return [_parse_drug(d) for d in results]

    except Exception as exc:
        logger.error("[OpenFDA] search_drug error: %s", exc)
        return []


def _parse_drug(d: dict) -> dict:
    """Extract the most useful fields from an FDA label record."""
    fda = d.get("openfda", {})
    return {
        "brand_name":        _safe(fda, "brand_name"),
        "generic_name":      _safe(fda, "generic_name"),
        "manufacturer":      _safe(fda, "manufacturer_name"),
        "route":             _safe(fda, "route"),
        "product_type":      _safe(fda, "product_type"),
        "indications":       _safe(d, "indications_and_usage"),
        "dosage":            _safe(d, "dosage_and_administration"),
        "warnings":          _safe(d, "warnings"),
        "side_effects":      _safe(d, "adverse_reactions"),
        "contraindications": _safe(d, "contraindications"),
        "overdosage":        _safe(d, "overdosage"),
        "storage":           _safe(d, "storage_and_handling"),
    }
