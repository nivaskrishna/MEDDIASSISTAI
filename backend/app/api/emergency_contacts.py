from fastapi import APIRouter
from typing import List
from app.schemas.condition import EmergencyContact
from app.services.data_service import load_emergency_contacts

router = APIRouter()

@router.get("/", response_model=List[EmergencyContact])
async def get_emergency_contacts():
    contacts = load_emergency_contacts()
    return contacts
