from pydantic import BaseModel
from typing import List, Optional

class ConditionBase(BaseModel):
    condition_name: str
    symptoms: List[str]
    first_aid_instructions: str
    severity_level: str
    recommended_doctor_type: str
    image_prompt: Optional[str] = None

class ConditionCreate(ConditionBase):
    pass

class Condition(ConditionBase):
    id: int

    class Config:
        from_attributes = True

class EmergencyContact(BaseModel):
    name: str
    number: str
    description: str
    category: Optional[str] = "other"
