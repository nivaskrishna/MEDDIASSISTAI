from pydantic import BaseModel
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    query: str
    image: Optional[str] = None # Base64 encoded image string (e.g. data:image/jpeg;base64,...)

class StepImageItem(BaseModel):
    step_number: int
    step_text: str
    search_query: str
    image_url: Optional[str] = None   # None = frontend loads lazily via /api/image-gen/generate

class AnalyzeResponse(BaseModel):
    condition: str
    first_aid: str
    severity: str
    doctor_type: str
    image_prompt: Optional[str] = None
    symptoms: Optional[List[str]] = []
    step_images: Optional[List[StepImageItem]] = []
