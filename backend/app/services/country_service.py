"""
REST Countries Service
Fetches country data from restcountries.com (free, no key, ~250 countries).
https://restcountries.com/

Used to provide country-specific emergency numbers in EmergencyPanel.
"""
import httpx
import logging

logger = logging.getLogger(__name__)

_BASE = "https://restcountries.com/v3.1"

# Known emergency numbers per country (ISO2 code → numbers)
# Sourced from Wikipedia / country official sources.
# disease.sh and REST Countries don't return emergency numbers directly,
# so we maintain a curated mapping for common countries.
_EMERGENCY_MAP = {
    "IN": {"police": "100", "ambulance": "108", "fire": "101", "national": "112", "disaster": "1078"},
    "US": {"police": "911", "ambulance": "911", "fire": "911", "national": "911"},
    "GB": {"police": "999", "ambulance": "999", "fire": "999", "national": "999", "non_emergency": "101"},
    "AU": {"police": "000", "ambulance": "000", "fire": "000", "national": "000"},
    "CA": {"police": "911", "ambulance": "911", "fire": "911", "national": "911"},
    "DE": {"police": "110", "ambulance": "112", "fire": "112", "national": "112"},
    "FR": {"police": "17",  "ambulance": "15",  "fire": "18",  "national": "112"},
    "JP": {"police": "110", "ambulance": "119", "fire": "119", "national": "110"},
    "CN": {"police": "110", "ambulance": "120", "fire": "119", "national": "110"},
    "BR": {"police": "190", "ambulance": "192", "fire": "193", "national": "190"},
    "ZA": {"police": "10111", "ambulance": "10177", "fire": "10177", "national": "112"},
    "AE": {"police": "999", "ambulance": "998", "fire": "997", "national": "999"},
    "SG": {"police": "999", "ambulance": "995", "fire": "995", "national": "999"},
    "PK": {"police": "15",  "ambulance": "1122", "fire": "16", "national": "112"},
    "BD": {"police": "999", "ambulance": "999", "fire": "999", "national": "999"},
    "NG": {"police": "199", "ambulance": "199", "fire": "199", "national": "199"},
    "DEFAULT": {"national": "112", "ambulance": "112", "police": "112", "fire": "112"},
}


async def get_country_info(iso2: str) -> dict:
    """
    Fetch basic country info from REST Countries API and merge with
    our emergency numbers mapping.

    Args:
        iso2: ISO 3166-1 alpha-2 country code (e.g. "IN", "US")
    """
    iso2 = iso2.upper().strip()
    url = f"{_BASE}/alpha/{iso2}?fields=name,cca2,cca3,flags,idd,capital,region,subregion,population"

    logger.info("[RestCountries] Fetching info for: %s", iso2)
    country_data = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                raw = r.json()
                idd = raw.get("idd", {})
                calling_code = ""
                if idd.get("root"):
                    suffixes = idd.get("suffixes", [""])
                    calling_code = idd["root"] + (suffixes[0] if suffixes else "")

                country_data = {
                    "name":         raw.get("name", {}).get("common", iso2),
                    "iso2":         iso2,
                    "iso3":         raw.get("cca3", ""),
                    "flag":         raw.get("flags", {}).get("svg", ""),
                    "flag_emoji":   raw.get("flags", {}).get("emoji", "🏳️"),
                    "capital":      (raw.get("capital") or [""])[0],
                    "region":       raw.get("region", ""),
                    "calling_code": calling_code,
                }
    except Exception as exc:
        logger.warning("[RestCountries] Could not fetch data for %s: %s", iso2, exc)

    # Merge emergency numbers
    emergency = _EMERGENCY_MAP.get(iso2, _EMERGENCY_MAP["DEFAULT"])
    return {**country_data, "emergency": emergency}


async def get_emergency_numbers(iso2: str) -> dict:
    """Return just the emergency numbers for a country code."""
    iso2 = iso2.upper().strip()
    return _EMERGENCY_MAP.get(iso2, _EMERGENCY_MAP["DEFAULT"])
