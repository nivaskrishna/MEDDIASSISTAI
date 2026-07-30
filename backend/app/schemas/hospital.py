from pydantic import BaseModel
from typing import List, Optional

class Hospital(BaseModel):
    name: str
    address: Optional[str] = "Address not available"
    distance_km: float
    latitude: float
    longitude: float

class LocationCenter(BaseModel):
    lat: float
    lon: float

class HospitalSearchResponse(BaseModel):
    center: LocationCenter
    hospitals: List[Hospital]
