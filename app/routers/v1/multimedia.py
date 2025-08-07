"""
Multimedia upload endpoints for flashcards.
Handles image and audio file uploads with validation and storage.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from typing import Optional
import logging
import os
from pathlib import Path

from app.core.deps import get_current_user
from app.services.multimedia_service import MultimediaService
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multimedia", tags=["multimedia"])

# Initialize service
multimedia_service = MultimediaService()

@router.post("/flashcards/{flashcard_id}/upload/question-image")
async def upload_question_image(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload image for flashcard question side."""
    try:
        file_url = await multimedia_service.upload_flashcard_media(
            flashcard_id=flashcard_id,
            file=file,
            media_type="question_image",
            user_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.email} uploaded question image for flashcard {flashcard_id}")
        
        return {
            "message": "Question image uploaded successfully",
            "file_url": file_url,
            "flashcard_id": flashcard_id,
            "media_type": "question_image"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading question image for flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@router.post("/flashcards/{flashcard_id}/upload/answer-image")
async def upload_answer_image(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload image for flashcard answer side."""
    try:
        file_url = await multimedia_service.upload_flashcard_media(
            flashcard_id=flashcard_id,
            file=file,
            media_type="answer_image",
            user_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.email} uploaded answer image for flashcard {flashcard_id}")
        
        return {
            "message": "Answer image uploaded successfully",
            "file_url": file_url,
            "flashcard_id": flashcard_id,
            "media_type": "answer_image"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading answer image for flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@router.post("/flashcards/{flashcard_id}/upload/question-audio")
async def upload_question_audio(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload audio for flashcard question side."""
    try:
        file_url = await multimedia_service.upload_flashcard_media(
            flashcard_id=flashcard_id,
            file=file,
            media_type="question_audio",
            user_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.email} uploaded question audio for flashcard {flashcard_id}")
        
        return {
            "message": "Question audio uploaded successfully",
            "file_url": file_url,
            "flashcard_id": flashcard_id,
            "media_type": "question_audio"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading question audio for flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload audio")

@router.post("/flashcards/{flashcard_id}/upload/answer-audio")
async def upload_answer_audio(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload audio for flashcard answer side."""
    try:
        file_url = await multimedia_service.upload_flashcard_media(
            flashcard_id=flashcard_id,
            file=file,
            media_type="answer_audio",
            user_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.email} uploaded answer audio for flashcard {flashcard_id}")
        
        return {
            "message": "Answer audio uploaded successfully",
            "file_url": file_url,
            "flashcard_id": flashcard_id,
            "media_type": "answer_audio"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading answer audio for flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload audio")

@router.delete("/flashcards/{flashcard_id}/media/{media_type}")
async def delete_flashcard_media(
    flashcard_id: str,
    media_type: str,
    current_user: User = Depends(get_current_user)
):
    """Delete specific media from flashcard."""
    try:
        success = await multimedia_service.delete_flashcard_media(
            flashcard_id=flashcard_id,
            media_type=media_type,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Media not found")
        
        logger.info(f"User {current_user.email} deleted {media_type} from flashcard {flashcard_id}")
        
        return {
            "message": f"{media_type} deleted successfully",
            "flashcard_id": flashcard_id,
            "media_type": media_type
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting {media_type} from flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete media")

@router.get("/files/{file_path:path}")
async def serve_media_file(file_path: str):
    """Serve uploaded media files."""
    try:
        full_path = multimedia_service.get_file_path(file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(full_path)
        
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve file")
