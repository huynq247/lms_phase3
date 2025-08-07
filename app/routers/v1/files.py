from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List
import os
from app.utils.file_service import file_service
from app.config import settings

router = APIRouter()

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file."""
    try:
        file_path = await file_service.save_file(file, "image")
        file_url = file_service.get_file_url(file_path)
        
        return {
            "message": "Image uploaded successfully",
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_url": file_url,
            "file_type": "image"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file."""
    try:
        file_path = await file_service.save_file(file, "audio")
        file_url = file_service.get_file_url(file_path)
        
        return {
            "message": "Audio uploaded successfully",
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_url": file_url,
            "file_type": "audio"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    """Download a file."""
    if file_type not in ["images", "audio"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = os.path.join(settings.upload_dir, file_type, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.delete("/delete/{file_type}/{filename}")
async def delete_file(file_type: str, filename: str):
    """Delete a file."""
    if file_type not in ["images", "audio"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = os.path.join(settings.upload_dir, file_type, filename)
    
    success = file_service.delete_file(file_path)
    
    if success:
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found or could not be deleted")

@router.get("/info/limits")
async def get_upload_limits():
    """Get file upload limits and allowed types."""
    return {
        "max_file_size": settings.max_file_size,
        "max_file_size_mb": settings.max_file_size / (1024 * 1024),
        "allowed_image_types": settings.allowed_image_types,
        "allowed_audio_types": settings.allowed_audio_types
    }
