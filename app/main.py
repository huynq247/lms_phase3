from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.utils.database import connect_to_mongo, close_mongo_connection, ping_database
from app.routers.v1 import health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Flashcard LMS Backend...")
    
    # Connect to database
    await connect_to_mongo()
    
    # Ensure upload directories exist
    from app.config import create_upload_dirs
    create_upload_dirs()
    
    logger.info("Startup completed successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_mongo_connection()
    logger.info("Shutdown completed")

# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="A comprehensive learning management system focused on flashcard-based learning with spaced repetition algorithm (SM-2).",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Include routers
app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["health"])

# Import and include auth router
from app.routers.v1 import auth
app.include_router(auth.router, prefix=settings.api_v1_prefix, tags=["authentication"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Flashcard LMS Backend API",
        "version": settings.version,
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    db_status = await ping_database()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": settings.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.reload,
        log_level="info"
    )
