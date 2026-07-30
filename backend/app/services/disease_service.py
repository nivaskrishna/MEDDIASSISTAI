"""
Disease Statistics Service
Fetches live global health data from disease.sh (completely free, no API key needed).
https://disease.sh/docs/
"""
import httpx
import logging

logger = logging.getLogger(__name__)

_BASE = "https://disease.sh/v3"
_HEADERS = {"Accept": "application/json"}


async def get_global_stats() -> dict:
    """
    Fetch worldwide COVID-19 totals.
    Returns a simplified dict with cases, deaths, recovered, active, updated.
    """
    url = f"{_BASE}/covid-19/all"
    logger.info("[disease.sh] Fetching global stats")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=_HEADERS)
            r.raise_for_status()
            data = r.json()
            return {
                "cases":       data.get("cases", 0),
                "deaths":      data.get("deaths", 0),
                "recovered":   data.get("recovered", 0),
                "active":      data.get("active", 0),
                "critical":    data.get("critical", 0),
                "updated":     data.get("updated", 0),
                "todayCases":  data.get("todayCases", 0),
                "todayDeaths": data.get("todayDeaths", 0),
                "population":  data.get("population", 0),
            }
    except Exception as exc:
        logger.error("[disease.sh] Failed to fetch global stats: %s", exc)
        return {}


async def get_country_stats(country: str) -> dict:
    """
    Fetch COVID stats for a specific country (name, ISO2, or ISO3 code).
    """
    url = f"{_BASE}/covid-19/countries/{country}"
    logger.info("[disease.sh] Fetching stats for country: %s", country)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=_HEADERS)
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            data = r.json()
            return {
                "country":    data.get("country", country),
                "flag":       data.get("countryInfo", {}).get("flag", ""),
                "cases":      data.get("cases", 0),
                "deaths":     data.get("deaths", 0),
                "recovered":  data.get("recovered", 0),
                "active":     data.get("active", 0),
                "critical":   data.get("critical", 0),
                "updated":    data.get("updated", 0),
            }
    except Exception as exc:
        logger.error("[disease.sh] Failed to fetch stats for %s: %s", country, exc)
        return {}
