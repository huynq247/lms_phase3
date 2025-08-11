"""Course models for Phase 5.3 - Course CRUD Operations"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from app.models.enums import DifficultyLevel

class CourseCreateRequest(BaseModel):
    """Request model for creating a course."""
    title: str = Field(..., min_length=3, max_length=200, description="Course title")
    description: str = Field(..., min_length=10, max_length=2000, description="Course description")
    category: str = Field(..., min_length=2, max_length=100, description="Course category")
    difficulty_level: DifficultyLevel = Field(..., description="Course difficulty level")
    is_public: bool = Field(default=True, description="Whether course is publicly visible")
    tags: List[str] = Field(default_factory=list, description="Course tags for searching")
    estimated_hours: Optional[int] = Field(None, ge=1, le=1000, description="Estimated completion hours")
    prerequisites: List[str] = Field(default_factory=list, description="Course prerequisites")
    
    @validator('tags', pre=True)
    def validate_tags(cls, v):
        if isinstance(v, list):
            # Remove duplicates and empty strings
            return list(set([tag.strip() for tag in v if tag.strip()]))
        return []
    
    @validator('prerequisites', pre=True)
    def validate_prerequisites(cls, v):
        if isinstance(v, list):
            return [prereq.strip() for prereq in v if prereq.strip()]
        return []

class CourseUpdateRequest(BaseModel):
    """Request model for updating a course."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    difficulty_level: Optional[DifficultyLevel] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    estimated_hours: Optional[int] = Field(None, ge=1, le=1000)
    prerequisites: Optional[List[str]] = None
    
    @validator('tags', pre=True)
    def validate_tags(cls, v):
        if v is not None and isinstance(v, list):
            return list(set([tag.strip() for tag in v if tag.strip()]))
        return v
    
    @validator('prerequisites', pre=True)
    def validate_prerequisites(cls, v):
        if v is not None and isinstance(v, list):
            return [prereq.strip() for prereq in v if prereq.strip()]
        return v

class CourseResponse(BaseModel):
    """Response model for course data."""
    id: str = Field(..., alias="_id")
    title: str
    description: str
    category: str
    difficulty_level: DifficultyLevel
    is_public: bool
    tags: List[str]
    estimated_hours: Optional[int]
    prerequisites: List[str]
    creator_id: str
    creator_name: str
    enrollments_count: int = Field(default=0)
    average_rating: Optional[float] = Field(default=None)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CourseListResponse(BaseModel):
    """Response model for course list items."""
    id: str = Field(..., alias="_id")
    title: str
    description: str
    category: str
    difficulty_level: DifficultyLevel
    is_public: bool
    tags: List[str]
    estimated_hours: Optional[int]
    creator_name: str
    enrollments_count: int = Field(default=0)
    average_rating: Optional[float] = Field(default=None)
    created_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CourseFilterRequest(BaseModel):
    """Request model for filtering courses."""
    category: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    is_public: Optional[bool] = None
    creator_id: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = Field(None, description="Search in title and description")
    
class CoursesListResponse(BaseModel):
    """Response model for paginated course list."""
    courses: List[CourseListResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

class CourseStatsResponse(BaseModel):
    """Response model for course statistics."""
    total_courses: int
    public_courses: int
    private_courses: int
    categories: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    top_creators: List[Dict[str, Any]]
