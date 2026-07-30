import httpx
import math
import logging
import re

logger = logging.getLogger(__name__)

# Haversine formula to calculate distance
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

async def geocode_query(query: str):
    query_clean = query.strip()
    headers = {"User-Agent": "MediAssist-AI/1.0"}
    
    # Check if 5 or 6 digit pincode
    is_pincode = re.match(r"^\d{5,6}$", query_clean)
    
    if is_pincode:
        # 1. Try querying data.gov.in API using user's keys
        resource_id = "579b464d-b66e-c23b-dd00-000136e124ed"
        api_key = "57ed496b690f77848ab71b08"
        gov_url = f"https://api.data.gov.in/resource/{resource_id}?api-key={api_key}&format=json&filters[pincode]={query_clean}"
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Attempting data.gov.in lookup for pincode: {query_clean}")
                resp = await client.get(gov_url, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    gov_data = resp.json()
                    records = gov_data.get("records", [])
                    if records:
                        first = records[0]
                        office = first.get("officename", "")
                        district = first.get("districtname", "")
                        state = first.get("statename", "")
                        location_q = f"{office}, {district}, {state}, India".replace(", ,", ",")
                        
                        nom_url = f"https://nominatim.openstreetmap.org/search?q={location_q}&countrycodes=in&format=json"
                        nom_resp = await client.get(nom_url, headers=headers)
                        nom_data = nom_resp.json()
                        if nom_data:
                            logger.info(f"Resolved data.gov.in location via Nominatim: {location_q}")
                            return float(nom_data[0]["lat"]), float(nom_data[0]["lon"])
        except Exception as ex:
            logger.warning(f"data.gov.in API lookup failed: {ex}. Trying next method...")

        # 2. Try Nominatim direct postal code lookup restricted to India
        url = f"https://nominatim.openstreetmap.org/search?postalcode={query_clean}&countrycodes=in&format=json"
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Attempting Nominatim postalcode lookup for: {query_clean}")
                resp = await client.get(url, headers=headers, timeout=5.0)
                data = resp.json()
                if data and len(data) > 0:
                    logger.info(f"Resolved via Nominatim postalcode search: {query_clean}")
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            logger.warning(f"Nominatim postalcode lookup error: {e}. Trying fallback postal API...")

        # 3. Fallback to free postalpincode.in API to get district and state
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Attempting postalpincode.in lookup for: {query_clean}")
                p_resp = await client.get(f"https://api.postalpincode.in/pincode/{query_clean}", headers=headers, timeout=5.0)
                if p_resp.status_code == 200:
                    p_data = p_resp.json()
                    if p_data and p_data[0].get("Status") == "Success":
                        po_list = p_data[0].get("PostOffice", [])
                        if po_list:
                            district = po_list[0].get("District")
                            state = po_list[0].get("State")
                            fallback_q = f"{district}, {state}, India"
                            logger.info(f"Resolved pincode via public API to: {fallback_q}")
                            f_url = f"https://nominatim.openstreetmap.org/search?q={fallback_q}&countrycodes=in&format=json"
                            f_resp = await client.get(f_url, headers=headers)
                            f_data = f_resp.json()
                            if f_data and len(f_data) > 0:
                                return float(f_data[0]["lat"]), float(f_data[0]["lon"])
        except Exception as ex:
            logger.error(f"Public pincode geocoding fallback failed: {ex}")
            
    else:
        # Search by general query (city, village, cross roads like malakvemula cross)
        # We append ', India' if 'india' is not already mentioned, and restrict countrycodes to 'in'
        search_q = query_clean
        if not re.search(r"\bindia\b", query_clean, re.IGNORECASE):
            search_q = f"{query_clean}, India"
            
        url = f"https://nominatim.openstreetmap.org/search?q={search_q}&countrycodes=in&format=json"
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Attempting general India search: {search_q}")
                resp = await client.get(url, headers=headers, timeout=6.0)
                data = resp.json()
                if data and len(data) > 0:
                    logger.info(f"Resolved general location: {search_q} -> {data[0]['lat']}, {data[0]['lon']}")
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            logger.error(f"General location geocoding error: {e}")
            
    return None, None

async def find_nearby_hospitals(lat: float, lon: float, radius_km: float):
    # Convert radius to meters
    radius_m = radius_km * 1000
    
    # Overpass QL query: nwr searches nodes, ways, and relations for hospitals/clinics.
    # out center; returns center coordinates for ways and relations.
    query = f"""
    [out:json];
    (
      nwr["amenity"="hospital"](around:{radius_m},{lat},{lon});
      nwr["amenity"="clinic"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter"
    ]
    
    headers = {"User-Agent": "MediAssist-AI/1.0"}
    
    for url in endpoints:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, data={"data": query}, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Overpass endpoint {url} returned status code {resp.status_code}, trying next...")
                    continue
                    
                data = resp.json()
                hospitals = []
                for element in data.get("elements", []):
                    # Try getting node coordinates first
                    h_lat = element.get("lat")
                    h_lon = element.get("lon")
                    
                    # Fallback to center coordinates if it's a way/relation
                    if h_lat is None or h_lon is None:
                        center = element.get("center", {})
                        h_lat = center.get("lat")
                        h_lon = center.get("lon")
                    
                    if h_lat is None or h_lon is None:
                        continue
                    
                    tags = element.get("tags", {})
                    name = tags.get("name", tags.get("operator", "Hospital/Clinic"))
                    address = f"{tags.get('addr:street', '')} {tags.get('addr:city', '')}".strip()
                    if not address:
                        address = tags.get("addr:full", "Address not available")
                    
                    dist = calculate_distance(lat, lon, h_lat, h_lon)
                    
                    hospitals.append({
                        "name": name,
                        "address": address,
                        "distance_km": round(dist, 2),
                        "latitude": h_lat,
                        "longitude": h_lon
                    })
                
                # Sort by distance
                hospitals.sort(key=lambda x: x["distance_km"])
                return hospitals
            except Exception as e:
                logger.error(f"Overpass API Error on {url}: {e}")
                continue # Try the next endpoint
                
    # If all endpoints fail
    logger.error("All Overpass API endpoints failed.")
    return []
