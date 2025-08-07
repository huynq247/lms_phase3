"""
Extended user profile model definitions.
"""
from datetime import datetime, time
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from enum import Enum


class LearningStyle(str, Enum):
    """Learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory" 
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class DifficultyLevel(str, Enum):
    """Difficulty level preferences."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StudyDayOfWeek(str, Enum):
    """Days of the week for study schedule."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class LearningPreferences(BaseModel):
    """User learning preferences."""
    learning_style: Optional[LearningStyle] = None
    preferred_difficulty: Optional[DifficultyLevel] = DifficultyLevel.BEGINNER
    cards_per_session: int = Field(default=20, ge=5, le=100)
    enable_timer: bool = True
    auto_advance: bool = False
    show_hints: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "learning_style": "visual",
                "preferred_difficulty": "beginner", 
                "cards_per_session": 20,
                "enable_timer": True,
                "auto_advance": False,
                "show_hints": True
            }
        }
    )


class LearningGoal(BaseModel):
    """Individual learning goal."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    is_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Master 100 Vietnamese vocabulary words",
                "description": "Focus on daily use words",
                "target_date": "2024-12-31T00:00:00",
                "is_completed": False
            }
        }
    )


class StudySession(BaseModel):
    """Study session configuration."""
    day_of_week: StudyDayOfWeek
    start_time: time = Field(..., description="Start time in HH:MM format")
    duration_minutes: int = Field(..., ge=15, le=480, description="Duration in minutes")
    is_active: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "day_of_week": "monday",
                "start_time": "19:00",
                "duration_minutes": 60,
                "is_active": True
            }
        }
    )


class Achievement(BaseModel):
    """User achievement."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    description: str
    icon: str
    unlocked_at: datetime = Field(default_factory=datetime.utcnow)
    category: str = "general"  # general, vocabulary, consistency, speed, etc.
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "First Steps",
                "description": "Created your first flashcard deck",
                "icon": "🎯",
                "category": "general"
            }
        }
    )


class StudyStatistics(BaseModel):
    """User study statistics."""
    total_study_time_minutes: int = 0
    total_cards_studied: int = 0
    total_decks_created: int = 0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    accuracy_percentage: float = 0.0
    last_study_date: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_study_time_minutes": 1200,
                "total_cards_studied": 450,
                "total_decks_created": 5,
                "current_streak_days": 7,
                "longest_streak_days": 15,
                "accuracy_percentage": 85.5,
                "last_study_date": "2024-01-15T10:30:00"
            }
        }
    )


# Extended User Profile Schemas

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile with extended features."""
    # Basic profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Extended profile fields
    learning_preferences: Optional[LearningPreferences] = None
    learning_goals: Optional[List[LearningGoal]] = None
    study_schedule: Optional[List[StudySession]] = None
    achievements: Optional[List[Achievement]] = None
    study_statistics: Optional[StudyStatistics] = None


class LearningGoalsUpdate(BaseModel):
    """Schema for updating learning goals."""
    learning_goals: List[LearningGoal] = Field(default_factory=list)


class StudyScheduleUpdate(BaseModel):
    """Schema for updating study schedule."""
    study_schedule: List[StudySession] = Field(default_factory=list)


class UserProfileResponse(BaseModel):
    """Extended user profile response."""
    id: str = Field(alias="_id")
    username: str
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # Extended profile fields
    learning_preferences: Optional[LearningPreferences] = None
    learning_goals: List[LearningGoal] = Field(default_factory=list)
    study_schedule: List[StudySession] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    study_statistics: Optional[StudyStatistics] = None
    
    model_config = ConfigDict(populate_by_name=True)


class AchievementsResponse(BaseModel):
    """Response for user achievements."""
    achievements: List[Achievement]
    total_count: int
    categories: Dict[str, int]  # Category -> count mapping
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "achievements": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "title": "First Steps",
                        "description": "Created your first flashcard deck",
                        "icon": "🎯",
                        "category": "general",
                        "unlocked_at": "2024-01-15T10:30:00"
                    }
                ],
                "total_count": 1,
                "categories": {"general": 1}
            }
        }
    )
