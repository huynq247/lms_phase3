"""
Lesson data models for Phase 5.5 Lesson CRUD Operations
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class LessonCompletionCriteria(BaseModel):
    """Completion criteria for a lesson"""
    type: str = Field(..., description="Type of completion criteria (time_based, quiz_based, manual)")
    min_duration_minutes: Optional[int] = Field(None, description="Minimum time to spend on lesson")
    required_quiz_score: Optional[int] = Field(None, description="Required quiz score to complete")
    require_manual_completion: bool = Field(False, description="Requires manual marking as complete")
    additional_requirements: Optional[Dict[str, Any]] = Field(None, description="Additional custom requirements")


class LessonBase(BaseModel):
    """Base lesson model with shared fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Lesson title")
    description: Optional[str] = Field(None, max_length=1000, description="Lesson description")
    content: Optional[str] = Field(None, description="Lesson content (markdown/HTML)")
    lesson_order: int = Field(..., ge=1, description="Order of lesson within course")
    duration_minutes: Optional[int] = Field(None, ge=1, le=600, description="Estimated lesson duration")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")
    prerequisite_lessons: List[str] = Field(default_factory=list, description="Required prerequisite lesson IDs")
    completion_criteria: Optional[LessonCompletionCriteria] = Field(None, description="How to complete lesson")
    pass_threshold: int = Field(70, ge=0, le=100, description="Minimum score to pass lesson")
    is_published: bool = Field(False, description="Whether lesson is published")

    @validator('learning_objectives')
    def validate_learning_objectives(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 learning objectives allowed')
        return v

    @validator('prerequisite_lessons')
    def validate_prerequisite_lessons(cls, v):
        if len(v) > 5:
            raise ValueError('Maximum 5 prerequisite lessons allowed')
        return v


class LessonCreate(LessonBase):
    """Model for creating a new lesson"""
    pass


class LessonUpdate(BaseModel):
    """Model for updating a lesson"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None)
    lesson_order: Optional[int] = Field(None, ge=1)
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    learning_objectives: Optional[List[str]] = Field(None)
    prerequisite_lessons: Optional[List[str]] = Field(None)
    completion_criteria: Optional[LessonCompletionCriteria] = Field(None)
    pass_threshold: Optional[int] = Field(None, ge=0, le=100)
    is_published: Optional[bool] = Field(None)

    @validator('learning_objectives')
    def validate_learning_objectives(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 learning objectives allowed')
        return v

    @validator('prerequisite_lessons')
    def validate_prerequisite_lessons(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError('Maximum 5 prerequisite lessons allowed')
        return v


class LessonResponse(LessonBase):
    """Model for lesson response"""
    id: str = Field(..., description="Lesson ID")
    course_id: str = Field(..., description="Course ID this lesson belongs to")
    created_by: str = Field(..., description="User ID who created the lesson")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(True, description="Whether lesson is active (not deleted)")

    @validator('id', 'course_id', 'created_by', pre=True)
    def convert_objectid_to_string(cls, v):
        """Convert ObjectId to string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


class LessonListResponse(BaseModel):
    """Model for lesson list response"""
    lessons: List[LessonResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class LessonOrderUpdate(BaseModel):
    """Model for updating lesson order"""
    lesson_id: str = Field(..., description="Lesson ID")
    new_order: int = Field(..., ge=1, description="New order position")


class LessonBulkOrderUpdate(BaseModel):
    """Model for bulk lesson order update"""
    order_updates: List[LessonOrderUpdate] = Field(..., min_items=1, max_items=50)


class LessonStatsResponse(BaseModel):
    """Model for lesson statistics"""
    total_lessons: int
    published_lessons: int
    draft_lessons: int
    avg_duration_minutes: Optional[float]
    total_duration_minutes: int
    lessons_with_prerequisites: int
    lessons_with_objectives: int


class LessonPrerequisiteCheck(BaseModel):
    """Model for prerequisite validation response"""
    lesson_id: str
    has_access: bool
    missing_prerequisites: List[str]
    completed_prerequisites: List[str]
