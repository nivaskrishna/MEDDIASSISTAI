from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.database import get_db
from app.db.models import Condition
from app.schemas.condition import Condition as ConditionSchema

router = APIRouter()

@router.get("/", response_model=List[ConditionSchema])
async def get_conditions(
    search: str = Query(None, description="Search condition by name"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Condition)
    if search:
        stmt = stmt.where(Condition.condition_name.ilike(f"%{search}%"))
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    conditions = result.scalars().all()
    return conditions

@router.get("/{condition_id}", response_model=ConditionSchema)
async def get_condition(condition_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Condition).where(Condition.id == condition_id))
    condition = result.scalars().first()
    if not condition:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Condition not found")
    return condition
