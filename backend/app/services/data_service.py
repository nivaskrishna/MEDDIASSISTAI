import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Condition, DoctorSpecialty
import logging

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

async def seed_database(db: AsyncSession):
    try:
        # Check if DB is already seeded
        result = await db.execute(select(Condition).limit(1))
        existing = result.scalars().first()
        if existing:
            logger.info("Database already seeded with conditions.")
            return

        conditions_file = DATA_DIR / "conditions.json"
        if not conditions_file.exists():
            logger.warning(f"Seed file not found at {conditions_file}")
            return

        with open(conditions_file, "r") as f:
            conditions_data = json.load(f)

        for item in conditions_data:
            condition = Condition(
                condition_name=item.get("condition") or item.get("Condition"),
                symptoms=item.get("symptoms") or item.get("Symptoms"),
                first_aid_instructions=item.get("firstAid") or item.get("FirstAid"),
                severity_level=item.get("severity") or item.get("Severity"),
                recommended_doctor_type=item.get("doctorType") or item.get("DoctorType"),
                image_prompt=item.get("imagePrompt") or item.get("image_prompt") or item.get("ImagePrompt")
            )
            db.add(condition)
        
        await db.commit()
        logger.info(f"Seeded {len(conditions_data)} conditions.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        await db.rollback()

def load_emergency_contacts():
    contacts_file = DATA_DIR / "emergency_contacts.json"
    if contacts_file.exists():
        with open(contacts_file, "r") as f:
            return json.load(f)
    return []
