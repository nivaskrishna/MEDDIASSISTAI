import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base, AsyncSessionLocal
from app.services.data_service import seed_database
import logging
from contextlib import asynccontextmanager

from app.api import analyze, hospitals, conditions, emergency_contacts, image_gen, disease, fda, country, history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        await seed_database(session)

    # Optional: MongoDB Atlas ping (fast-fail if LibreSSL incompatible)
    from app.db.mongo import ping_mongo
    await ping_mongo()
        
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api/analyze", tags=["Analyze"])
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["Hospitals"])
app.include_router(conditions.router, prefix="/api/conditions", tags=["Conditions"])
app.include_router(emergency_contacts.router, prefix="/api/emergency-contacts", tags=["Contacts"])
app.include_router(image_gen.router, prefix="/api/image-gen", tags=["Image Generation"])
app.include_router(disease.router, prefix="/api/disease", tags=["Disease Stats"])
app.include_router(fda.router, prefix="/api/fda", tags=["Drug Info"])
app.include_router(country.router, prefix="/api/country", tags=["Country Info"])
app.include_router(history.router, prefix="/api/history", tags=["History"])

from app.api.analyze import search_images_endpoint
from app.schemas.analyze import AnalyzeRequest

@app.post("/api/search-images")
async def root_search_images(request: AnalyzeRequest):
    return await search_images_endpoint(request)

@app.get("/")
async def root():
    return {"message": "Welcome to MediAssist AI API"}
