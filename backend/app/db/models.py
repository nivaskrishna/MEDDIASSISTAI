from sqlalchemy import Column, Integer, String, Text, JSON
from app.db.database import Base

class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    condition_name = Column(String, unique=True, index=True)
    symptoms = Column(JSON)  # Store as a JSON array of strings
    first_aid_instructions = Column(Text)
    severity_level = Column(String)
    recommended_doctor_type = Column(String)
    image_prompt = Column(Text, nullable=True)

class DoctorSpecialty(Base):
    __tablename__ = "doctor_specialties"

    id = Column(Integer, primary_key=True, index=True)
    specialty = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
