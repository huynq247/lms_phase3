"""
Deck model definitions with advanced privacy features.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from app.models.enums import UserRole


class DeckPrivacyLevel(str):
    """Deck privacy levels for advanced access control."""
    PRIVATE = "private"                    # Owner only
    CLASS_ASSIGNED = "class-assigned"      # Assigned to specific class
    COURSE_ASSIGNED = "course-assigned"    # Assigned to specific course  
    LESSON_ASSIGNED = "lesson-assigned"    # Assigned to specific lesson
    PUBLIC = "public"                      # Everyone can access


class DeckBase(BaseModel):
    """Base deck model with common fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    privacy_level: str = Field(default=DeckPrivacyLevel.PRIVATE)
    tags: List[str] = Field(default_factory=list, max_items=20)
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=600)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if not v:
            return []
        # Remove duplicates, strip whitespace, filter empty
        cleaned = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned[:20]  # Limit to 20 tags
    
    @validator('privacy_level')
    def validate_privacy_level(cls, v):
        """Validate privacy level."""
        valid_levels = [
            DeckPrivacyLevel.PRIVATE,
            DeckPrivacyLevel.CLASS_ASSIGNED,
            DeckPrivacyLevel.COURSE_ASSIGNED,
            DeckPrivacyLevel.LESSON_ASSIGNED,
            DeckPrivacyLevel.PUBLIC
        ]
        if v not in valid_levels:
            raise ValueError(f"Privacy level must be one of: {valid_levels}")
        return v


class DeckCreateRequest(DeckBase):
    """Request to create a new deck."""
    # Assignment fields for privacy levels
    assigned_class_ids: Optional[List[str]] = Field(default_factory=list)
    assigned_course_ids: Optional[List[str]] = Field(default_factory=list)
    assigned_lesson_ids: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction to Python",
                "description": "Basic Python concepts for beginners",
                "privacy_level": "public",
                "tags": ["python", "programming", "beginner"],
                "difficulty_level": "beginner",
                "estimated_time_minutes": 30,
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            }
        }


class DeckUpdateRequest(BaseModel):
    """Request to update an existing deck."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    privacy_level: Optional[str] = None
    tags: Optional[List[str]] = Field(None, max_items=20)
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=600)
    assigned_class_ids: Optional[List[str]] = None
    assigned_course_ids: Optional[List[str]] = None
    assigned_lesson_ids: Optional[List[str]] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if v is None:
            return None
        # Remove duplicates, strip whitespace, filter empty
        cleaned = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned[:20]  # Limit to 20 tags
    
    @validator('privacy_level')
    def validate_privacy_level(cls, v):
        """Validate privacy level."""
        if v is None:
            return None
        valid_levels = [
            DeckPrivacyLevel.PRIVATE,
            DeckPrivacyLevel.CLASS_ASSIGNED,
            DeckPrivacyLevel.COURSE_ASSIGNED,
            DeckPrivacyLevel.LESSON_ASSIGNED,
            DeckPrivacyLevel.PUBLIC
        ]
        if v not in valid_levels:
            raise ValueError(f"Privacy level must be one of: {valid_levels}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Advanced Python Concepts",
                "description": "Deep dive into Python advanced features",
                "privacy_level": "class-assigned",
                "tags": ["python", "advanced", "oop"],
                "difficulty_level": "advanced",
                "estimated_time_minutes": 60,
                "assigned_class_ids": ["507f1f77bcf86cd799439011"]
            }
        }


class DeckResponse(BaseModel):
    """Deck response model."""
    id: str = Field(alias="_id")
    title: str
    description: Optional[str] = None
    privacy_level: str
    tags: List[str]
    difficulty_level: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    
    # Owner information
    owner_id: str
    owner_username: str
    
    # Assignment information
    assigned_class_ids: List[str]
    assigned_course_ids: List[str]
    assigned_lesson_ids: List[str]
    
    # Metadata
    total_cards: int = 0
    is_favorite: bool = False  # If current user has favorited this deck
    can_edit: bool = False     # If current user can edit this deck
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Introduction to Python",
                "description": "Basic Python concepts for beginners",
                "privacy_level": "public",
                "tags": ["python", "programming", "beginner"],
                "difficulty_level": "beginner",
                "estimated_time_minutes": 30,
                "owner_id": "507f1f77bcf86cd799439012",
                "owner_username": "teacher_user",
                "assigned_class_ids": [],
                "assigned_course_ids": [],
                "assigned_lesson_ids": [],
                "total_cards": 15,
                "is_favorite": False,
                "can_edit": False,
                "created_at": "2025-08-08T10:30:00",
                "updated_at": "2025-08-08T10:30:00"
            }
        }


class DeckListResponse(BaseModel):
    """Paginated deck list response with privacy filtering."""
    decks: List[DeckResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    # Filter information
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "decks": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "title": "Introduction to Python",
                        "privacy_level": "public",
                        "owner_username": "teacher_user",
                        "total_cards": 15,
                        "can_edit": False
                    }
                ],
                "total_count": 25,
                "page": 1,
                "limit": 10,
                "total_pages": 3,
                "has_next": True,
                "has_prev": False,
                "applied_filters": {
                    "privacy_level": "public",
                    "tags": ["python"],
                    "difficulty_level": "beginner"
                }
            }
        }


class DeckAccessInfo(BaseModel):
    """Information about user's access to a deck."""
    can_view: bool
    can_edit: bool
    can_delete: bool
    access_reason: str  # "owner", "public", "class_assigned", "course_assigned", "lesson_assigned"
    
    class Config:
        json_schema_extra = {
            "example": {
                "can_view": True,
                "can_edit": False,
                "can_delete": False,
                "access_reason": "public"
            }
        }


class DeckStatistics(BaseModel):
    """Deck usage statistics."""
    total_views: int = 0
    total_studies: int = 0
    average_rating: float = 0.0
    total_ratings: int = 0
    completion_rate: float = 0.0
    last_studied: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_views": 150,
                "total_studies": 45,
                "average_rating": 4.2,
                "total_ratings": 12,
                "completion_rate": 78.5,
                "last_studied": "2025-08-07T15:30:00"
            }
        }
