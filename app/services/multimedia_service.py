"""
Multimedia service for handling file uploads and storage.
Supports images and audio files for flashcards.
"""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException
from bson import ObjectId
import logging
from datetime import datetime

from app.utils.database import get_users_collection, get_flashcards_collection, get_decks_collection
from app.models.user import UserRole

logger = logging.getLogger(__name__)

class MultimediaService:
    """Service for handling multimedia uploads and storage."""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.image_dir = self.upload_dir / "images"
        self.audio_dir = self.upload_dir / "audio"
        
        # Create directories if they don't exist
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # File type restrictions
        self.allowed_image_types = {
            "image/jpeg", "image/jpg", "image/png", 
            "image/gif", "image/webp"
        }
        self.allowed_audio_types = {
            "audio/mpeg", "audio/mp3", "audio/wav", 
            "audio/ogg", "audio/m4a"
        }
        
        # File size limits (10MB)
        self.max_file_size = 10 * 1024 * 1024

    def _get_collections(self):
        """Get database collections (lazy initialization)."""
        return {
            'flashcards': get_flashcards_collection(),
            'decks': get_decks_collection(),
            'users': get_users_collection()
        }

    async def upload_flashcard_media(
        self, 
        flashcard_id: str, 
        file: UploadFile, 
        media_type: str,
        user_id: str
    ) -> str:
        """Upload media file for a flashcard."""
        try:
            # Validate flashcard exists and user has permission
            await self._validate_flashcard_permission(flashcard_id, user_id)
            
            # Validate file
            await self._validate_file(file, media_type)
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Determine storage directory
            if "image" in media_type:
                storage_dir = self.image_dir
            else:
                storage_dir = self.audio_dir
            
            file_path = storage_dir / unique_filename
            
            # Save file
            await self._save_file(file, file_path)
            
            # Update flashcard with media URL
            media_url = f"/api/v1/multimedia/files/{storage_dir.name}/{unique_filename}"
            await self._update_flashcard_media(flashcard_id, media_type, media_url)
            
            logger.info(f"Successfully uploaded {media_type} for flashcard {flashcard_id}")
            return media_url
            
        except Exception as e:
            logger.error(f"Error uploading media for flashcard {flashcard_id}: {str(e)}")
            raise

    async def delete_flashcard_media(
        self, 
        flashcard_id: str, 
        media_type: str,
        user_id: str
    ) -> bool:
        """Delete media file from flashcard."""
        try:
            # Validate flashcard exists and user has permission
            await self._validate_flashcard_permission(flashcard_id, user_id)
            
            # Get current media URL
            collections = self._get_collections()
            flashcard = await collections['flashcards'].find_one(
                {"_id": ObjectId(flashcard_id)}
            )
            
            if not flashcard:
                raise ValueError("Flashcard not found")
            
            # Get media URL from flashcard content
            media_url = self._get_media_url_from_flashcard(flashcard, media_type)
            
            if not media_url:
                return False
            
            # Delete physical file
            if media_url.startswith("/api/v1/multimedia/files/"):
                file_path = self._get_physical_file_path(media_url)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Remove media URL from flashcard
            await self._remove_flashcard_media(flashcard_id, media_type)
            
            logger.info(f"Successfully deleted {media_type} from flashcard {flashcard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting media from flashcard {flashcard_id}: {str(e)}")
            raise

    def get_file_path(self, file_path: str) -> str:
        """Get full file path for serving files."""
        return str(self.upload_dir / file_path)

    async def _validate_flashcard_permission(self, flashcard_id: str, user_id: str):
        """Validate user has permission to modify flashcard."""
        collections = self._get_collections()
        
        # Get flashcard
        flashcard = await collections['flashcards'].find_one(
            {"_id": ObjectId(flashcard_id)}
        )
        
        if not flashcard:
            raise ValueError("Flashcard not found")
        
        # Get deck
        deck = await collections['decks'].find_one(
            {"_id": ObjectId(flashcard["deck_id"])}
        )
        
        if not deck:
            raise ValueError("Deck not found")
        
        # Get user
        user = await collections['users'].find_one(
            {"_id": ObjectId(user_id)}
        )
        
        if not user:
            raise ValueError("User not found")
        
        # Check permissions
        user_role = UserRole(user["role"])
        
        # Admin can modify anything
        if user_role == UserRole.ADMIN:
            return
        
        # Deck creator can modify
        if str(deck["created_by"]) == user_id:
            return
        
        # Teachers can modify their assigned decks
        if user_role == UserRole.TEACHER:
            # Check if teacher is assigned to this deck
            # For now, allow teachers to modify any deck
            return
        
        raise PermissionError("Permission denied to modify this flashcard")

    async def _validate_file(self, file: UploadFile, media_type: str):
        """Validate uploaded file."""
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer
        
        if file_size > self.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024):.1f}MB")
        
        # Check file type
        if "image" in media_type:
            if file.content_type not in self.allowed_image_types:
                raise ValueError(f"Invalid image type. Allowed types: {', '.join(self.allowed_image_types)}")
        elif "audio" in media_type:
            if file.content_type not in self.allowed_audio_types:
                raise ValueError(f"Invalid audio type. Allowed types: {', '.join(self.allowed_audio_types)}")
        else:
            raise ValueError("Invalid media type")

    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        if not filename:
            return ""
        return Path(filename).suffix.lower()

    async def _save_file(self, file: UploadFile, file_path: Path):
        """Save uploaded file to disk."""
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

    async def _update_flashcard_media(self, flashcard_id: str, media_type: str, media_url: str):
        """Update flashcard with media URL."""
        collections = self._get_collections()
        update_data = {"updated_at": datetime.utcnow()}
        
        if media_type == "question_image":
            update_data["front.image_url"] = media_url
        elif media_type == "answer_image":
            update_data["back.image_url"] = media_url
        elif media_type == "question_audio":
            update_data["front.audio_url"] = media_url
        elif media_type == "answer_audio":
            update_data["back.audio_url"] = media_url
        
        await collections['flashcards'].update_one(
            {"_id": ObjectId(flashcard_id)},
            {"$set": update_data}
        )

    def _get_media_url_from_flashcard(self, flashcard: dict, media_type: str) -> Optional[str]:
        """Get media URL from flashcard content."""
        if media_type == "question_image":
            return flashcard.get("front", {}).get("image_url")
        elif media_type == "answer_image":
            return flashcard.get("back", {}).get("image_url")
        elif media_type == "question_audio":
            return flashcard.get("front", {}).get("audio_url")
        elif media_type == "answer_audio":
            return flashcard.get("back", {}).get("audio_url")
        return None

    def _get_physical_file_path(self, media_url: str) -> str:
        """Convert media URL to physical file path."""
        # Remove API prefix to get relative path
        relative_path = media_url.replace("/api/v1/multimedia/files/", "")
        return str(self.upload_dir / relative_path)

    async def _remove_flashcard_media(self, flashcard_id: str, media_type: str):
        """Remove media URL from flashcard."""
        collections = self._get_collections()
        unset_data = {}
        
        if media_type == "question_image":
            unset_data["front.image_url"] = ""
        elif media_type == "answer_image":
            unset_data["back.image_url"] = ""
        elif media_type == "question_audio":
            unset_data["front.audio_url"] = ""
        elif media_type == "answer_audio":
            unset_data["back.audio_url"] = ""
        
        update_data = {
            "$unset": unset_data,
            "$set": {"updated_at": datetime.utcnow()}
        }
        
        await collections['flashcards'].update_one(
            {"_id": ObjectId(flashcard_id)},
            update_data
        )
