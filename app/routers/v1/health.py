from fastapi import APIRouter, Depends
from datetime import datetime
from app.utils.database import ping_database, get_database

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Flashcard LMS Backend",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db = Depends(get_database)):
    """Detailed health check with database status."""
    
    # Check database connection
    db_connected = await ping_database()
    
    health_status = {
        "status": "healthy" if db_connected else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Flashcard LMS Backend",
        "version": "1.0.0",
        "checks": {
            "database": {
                "status": "up" if db_connected else "down",
                "type": "MongoDB"
            }
        }
    }
    
    return health_status

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    db_connected = await ping_database()
    
    if not db_connected:
        return {"status": "not ready", "reason": "database not connected"}, 503
    
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}
