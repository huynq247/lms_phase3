from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
from app.utils.database import ping_database, get_database
from app.utils.response_standardizer import ResponseStandardizer

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    response_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Flashcard LMS Backend",
        "version": "1.0.0"
    }
    
    # Standardize response format (_id -> id)
    response_dict = jsonable_encoder(response_data)
    return ResponseStandardizer.create_standardized_response(response_dict)

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
    
    # Standardize response format (_id -> id)
    response_dict = jsonable_encoder(health_status)
    return ResponseStandardizer.create_standardized_response(response_dict)

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    db_connected = await ping_database()
    
    if not db_connected:
        response_data = {"status": "not ready", "reason": "database not connected"}
        response_dict = jsonable_encoder(response_data)
        return ResponseStandardizer.create_standardized_response(response_dict), 503
    
    response_data = {"status": "ready"}
    response_dict = jsonable_encoder(response_data)
    return ResponseStandardizer.create_standardized_response(response_dict)

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    response_data = {"status": "alive"}
    response_dict = jsonable_encoder(response_data)
    return ResponseStandardizer.create_standardized_response(response_dict)
