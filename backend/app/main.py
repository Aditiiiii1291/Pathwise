import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from app.core.database import init_db
    import app.models
    from app.api.api import api_router
except ImportError:
    from backend.app.core.database import init_db
    import backend.app.models
    from backend.app.api.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Pathwise API",
    description="Early Warning & Intervention Intelligence for Student Retention",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for local development
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "project": "Pathwise",
        "description": "Early Warning & Intervention Intelligence for Student Retention",
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "pathwise-api"
    }
