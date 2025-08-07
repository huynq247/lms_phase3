from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "flashcard_lms_db"
    
    # Security
    secret_key: str = "your-super-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Services
    gemini_api_key: str = ""
    
    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_image_types: str = "jpg,jpeg,png,gif"
    allowed_audio_types: str = "mp3,wav,m4a"
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Flashcard LMS Backend"
    version: str = "1.0.0"
    
    # Development
    debug: bool = True
    reload: bool = True
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Get allowed image types as list."""
        return [t.strip() for t in self.allowed_image_types.split(",")]
    
    @property
    def allowed_audio_types_list(self) -> List[str]:
        """Get allowed audio types as list."""
        return [t.strip() for t in self.allowed_audio_types.split(",")]
    
    model_config = {
        'env_file': os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
        'env_file_encoding': 'utf-8',
        'case_sensitive': False,
        'extra': 'allow'
    }

# Create global settings instance
settings = Settings()

# Ensure upload directories exist
def create_upload_dirs():
    """Create upload directories if they don't exist."""
    upload_path = settings.upload_dir
    images_path = os.path.join(upload_path, "images")
    audio_path = os.path.join(upload_path, "audio")
    
    os.makedirs(images_path, exist_ok=True)
    os.makedirs(audio_path, exist_ok=True)
    
    # Create .gitkeep files to track empty directories
    for path in [images_path, audio_path]:
        gitkeep_file = os.path.join(path, ".gitkeep")
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, "w") as f:
                f.write("")

# Initialize upload directories
create_upload_dirs()
