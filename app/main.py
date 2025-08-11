from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
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

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

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

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

# Import and include profile router
from app.routers.v1 import profile
app.include_router(profile.router, prefix=settings.api_v1_prefix, tags=["user-profile"])

# Import and include admin router
from app.routers.v1 import admin
app.include_router(admin.router, prefix=settings.api_v1_prefix, tags=["admin-management"])

# Import and include deck router
from app.routers.v1 import deck
app.include_router(deck.router, prefix=settings.api_v1_prefix, tags=["deck-management"])

# Import and include category router
from app.routers.v1 import category
app.include_router(category.router, prefix=settings.api_v1_prefix, tags=["category-management"])

# Import and include assignment router
from app.routers.v1 import assignment
app.include_router(assignment.router, prefix=settings.api_v1_prefix, tags=["assignment-management"])

# Import and include flashcard router
from app.routers.v1 import flashcard
app.include_router(flashcard.router, prefix=settings.api_v1_prefix, tags=["flashcard-management"])
app.include_router(flashcard.deck_router, prefix=settings.api_v1_prefix, tags=["flashcard-management"])

# Import and include multimedia router
from app.routers.v1 import multimedia
app.include_router(multimedia.router, prefix=settings.api_v1_prefix, tags=["multimedia-management"])

# Import and include classroom router (Phase 5.1)
from app.routers.v1 import classroom
app.include_router(classroom.router, prefix=settings.api_v1_prefix, tags=["class-management"])

# Import and include course router (Phase 5.3)
from app.routers.v1 import courses
app.include_router(courses.router, prefix=settings.api_v1_prefix, tags=["course-management"])

from app.routers.v1 import lessons
app.include_router(lessons.router, prefix=settings.api_v1_prefix, tags=["lesson-management"])

# Import and include lesson structure router (Phase 5.6)
from app.routers.v1 import lesson_structure
app.include_router(lesson_structure.router, prefix=settings.api_v1_prefix, tags=["lesson-structure"])

# Import and include lesson deck assignment router (Phase 5.6)
from app.routers.v1 import lesson_deck_assignments
app.include_router(lesson_deck_assignments.router, prefix=settings.api_v1_prefix, tags=["lesson-deck-assignments"])

# Import and include enrollment router (Phase 5.7)
from app.routers.v1 import enrollments
app.include_router(enrollments.router, prefix=settings.api_v1_prefix, tags=["multi-level-enrollment"])

# Import and include reports router (Phase 5.8)
from app.routers.v1 import reports
app.include_router(reports.router, prefix=settings.api_v1_prefix, tags=["enrollment-reporting"])

# Import and include study sessions router (Phase 6.1)
from app.routers.v1 import study_sessions
app.include_router(study_sessions.router, prefix=settings.api_v1_prefix, tags=["study-sessions"])

# Import and include progress analytics router (Phase 6.4)
from app.routers.v1 import progress_analytics
app.include_router(progress_analytics.router, prefix=settings.api_v1_prefix, tags=["progress-analytics"])

# Import and include analytics router (Phase 6.5)
from app.routers.v1 import analytics
app.include_router(analytics.router, prefix=settings.api_v1_prefix, tags=["analytics-charts"])

# Test comment to trigger reload

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
