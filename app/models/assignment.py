"""
Assignment model definitions for deck assignments.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class AssignmentType:
    """Assignment type constants."""
    CLASS = "class"
    COURSE = "course"
    LESSON = "lesson"


class DeckAssignmentBase(BaseModel):
    """Base assignment model."""
    deck_id: str = Field(..., description="Deck ID being assigned")
    assignment_type: str = Field(..., description="Type of assignment (class/course/lesson)")
    target_id: str = Field(..., description="ID of the target (class_id/course_id/lesson_id)")
    assigned_by: str = Field(..., description="User ID who made the assignment")


class DeckAssignmentCreate(DeckAssignmentBase):
    """Request to create a deck assignment."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "deck_id": "64a1b2c3d4e5f6789abcdef0",
                "assignment_type": "class",
                "target_id": "class_webdev",
                "assigned_by": "64a1b2c3d4e5f6789abcdef1"
            }
        }


class DeckAssignmentResponse(DeckAssignmentBase):
    """Response model for deck assignments."""
    id: str = Field(alias="_id")
    created_at: datetime
    deck_title: Optional[str] = Field(None, description="Title of the assigned deck")
    assigned_by_username: Optional[str] = Field(None, description="Username who made assignment")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "64a1b2c3d4e5f6789abcdef2",
                "deck_id": "64a1b2c3d4e5f6789abcdef0",
                "assignment_type": "class",
                "target_id": "class_webdev",
                "assigned_by": "64a1b2c3d4e5f6789abcdef1",
                "created_at": "2025-08-07T20:00:00.000Z",
                "deck_title": "Introduction to Python",
                "assigned_by_username": "teacher_user"
            }
        }


class DeckPrivacyUpdateRequest(BaseModel):
    """Request to update deck privacy level."""
    privacy_level: str = Field(..., description="New privacy level")
    assigned_class_ids: Optional[list[str]] = Field(default_factory=list)
    assigned_course_ids: Optional[list[str]] = Field(default_factory=list)
    assigned_lesson_ids: Optional[list[str]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "privacy_level": "class-assigned",
                "assigned_class_ids": ["class_webdev", "class_python"],
                "assigned_course_ids": [],
                "assigned_lesson_ids": []
            }
        }


class AssignmentListResponse(BaseModel):
    """Response for paginated assignment list."""
    assignments: list[DeckAssignmentResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
