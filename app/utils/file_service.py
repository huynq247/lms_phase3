import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image
from typing import Optional, List
from app.config import settings

class FileService:
    """Service for handling file uploads and validation."""
    
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.max_file_size = settings.max_file_size
        self.allowed_image_types = settings.allowed_image_types_list
        self.allowed_audio_types = settings.allowed_audio_types_list
    
    def validate_file_type(self, filename: str, file_type: str) -> bool:
        """Validate file type based on extension."""
        if not filename:
            return False
        
        file_extension = filename.lower().split('.')[-1]
        
        if file_type == "image":
            return file_extension in self.allowed_image_types
        elif file_type == "audio":
            return file_extension in self.allowed_audio_types
        
        return False
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size."""
        return file_size <= self.max_file_size
    
    def generate_filename(self, original_filename: str) -> str:
        """Generate unique filename."""
        file_extension = original_filename.lower().split('.')[-1]
        unique_id = str(uuid.uuid4())
        return f"{unique_id}.{file_extension}"
    
    async def save_file(self, file: UploadFile, file_type: str) -> str:
        """Save uploaded file and return the file path."""
        
        # Validate file type
        if not self.validate_file_type(file.filename, file_type):
            allowed_types = self.allowed_image_types if file_type == "image" else self.allowed_audio_types
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read file content to check size
        file_content = await file.read()
        
        # Validate file size
        if not self.validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.max_file_size} bytes"
            )
        
        # Generate unique filename
        filename = self.generate_filename(file.filename)
        
        # Determine save directory
        save_dir = os.path.join(self.upload_dir, f"{file_type}s")  # images or audios
        file_path = os.path.join(save_dir, filename)
        
        # Ensure directory exists
        os.makedirs(save_dir, exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        
        # For images, validate and potentially resize
        if file_type == "image":
            await self._process_image(file_path)
        
        return file_path
    
    async def _process_image(self, file_path: str):
        """Process and validate image file."""
        try:
            with Image.open(file_path) as img:
                # Validate that it's actually an image
                img.verify()
                
                # Reopen for processing (verify() closes the image)
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary (for JPEG compatibility)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    # Resize if too large (optional - maintain aspect ratio)
                    max_size = (1920, 1080)
                    if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        img.save(file_path, optimize=True, quality=85)
                        
        except Exception as e:
            # Remove invalid file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_url(self, file_path: str) -> str:
        """Get URL for accessing the file."""
        # This will be used with FastAPI static file serving
        return f"/uploads/{file_path.replace(self.upload_dir + os.sep, '').replace(os.sep, '/')}"

# Global file service instance
file_service = FileService()
