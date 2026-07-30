from fastapi import APIRouter, HTTPException, Query, Request
from app.schemas.hospital import HospitalSearchResponse, Hospital, LocationCenter
from app.services.map_service import geocode_query, find_nearby_hospitals
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/geolocation")
async def get_user_geolocation(request: Request):
    """Server-side IP geolocation - avoids CORS issues in the browser."""
    # Get client IP from headers (handles proxies/load balancers)
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or (request.client.host if request.client else "")
    )
    logger.info(f"Geolocation request from IP: {client_ip}")
    
    # Don't try to geolocate localhost/private IPs
    if not client_ip or client_ip in ("127.0.0.1", "::1", "localhost"):
        logger.info("Local/private IP detected — returning default India coordinates")
        return {"lat": 20.5937, "lon": 78.9629, "city": "India", "source": "default"}
    
    providers = [
        f"https://ipapi.co/{client_ip}/json/",
        f"https://ip-api.com/json/{client_ip}?fields=lat,lon,city,status",
    ]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Provider 1: ipapi.co
        try:
            resp = await client.get(providers[0])
            if resp.status_code == 200:
                data = resp.json()
                if data.get("latitude") and data.get("longitude"):
                    return {
                        "lat": data["latitude"], "lon": data["longitude"],
                        "city": data.get("city", ""), "source": "ipapi.co"
                    }
        except Exception as e:
            logger.warning(f"ipapi.co failed: {e}")
        
        # Provider 2: ip-api.com
        try:
            resp = await client.get(providers[1])
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return {
                        "lat": data["lat"], "lon": data["lon"],
                        "city": data.get("city", ""), "source": "ip-api.com"
                    }
        except Exception as e:
            logger.warning(f"ip-api.com failed: {e}")
    
    # Final fallback — center of India
    return {"lat": 20.5937, "lon": 78.9629, "city": "India", "source": "default"}


@router.get("/search", response_model=HospitalSearchResponse)
async def search_hospitals(
    query: str = Query(None, description="Pincode or location name to search near"),
    lat: float = Query(None, description="Latitude for coordinate search"),
    lon: float = Query(None, description="Longitude for coordinate search"),
    radius: float = Query(10.0, description="Radius in km (default 10)")
):
    if lat is not None and lon is not None:
        hospitals_data = await find_nearby_hospitals(lat, lon, radius)
        return HospitalSearchResponse(
            center=LocationCenter(lat=lat, lon=lon),
            hospitals=[Hospital(**h) for h in hospitals_data]
        )
        
    # Treat empty string same as None
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Either query or lat/lon coordinates must be provided")

    lat_resolved, lon_resolved = await geocode_query(query)
    if lat_resolved is None or lon_resolved is None:
        raise HTTPException(status_code=404, detail="Could not resolve pincode or location to coordinates")
    
    hospitals_data = await find_nearby_hospitals(lat_resolved, lon_resolved, radius)
    
    return HospitalSearchResponse(
        center=LocationCenter(lat=lat_resolved, lon=lon_resolved),
        hospitals=[Hospital(**h) for h in hospitals_data]
    )
