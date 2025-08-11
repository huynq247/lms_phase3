"""Class (Classroom) model definitions for Phase 5.1."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ClassCreateRequest(BaseModel):
    """Request schema to create a class."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    max_students: Optional[int] = Field(None, gt=0, le=1000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @validator("end_date")
    def validate_date_range(cls, v, values):  # type: ignore[override]
        start = values.get("start_date")
        if v and start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class ClassUpdateRequest(BaseModel):
    """Request schema to update a class."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    max_students: Optional[int] = Field(None, gt=0, le=1000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

    @validator("end_date")
    def validate_date_range(cls, v, values):  # type: ignore[override]
        start = values.get("start_date")
        if v and start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class ClassResponse(BaseModel):
    """Full class response."""
    id: str = Field(alias="_id")
    name: str
    description: Optional[str]
    teacher_id: str
    teacher_name: str
    student_ids: List[str] = []
    course_ids: List[str] = []
    max_students: Optional[int] = None
    current_enrollment: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class ClassListResponse(BaseModel):
    """Lightweight list item for class listing."""
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    teacher_name: str
    current_enrollment: int
    max_students: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        populate_by_name = True


# Enrollment Management Models for Phase 5.2

class EnrollmentRequest(BaseModel):
    """Request to enroll a student in a class."""
    user_id: str = Field(..., description="User ID to enroll")


class EnrollmentResponse(BaseModel):
    """Response after enrollment operation."""
    class_id: str
    user_id: str
    user_name: str
    enrollment_date: datetime
    status: str = "enrolled"


class BulkEnrollmentRequest(BaseModel):
    """Request for bulk enrollment via CSV."""
    csv_data: str = Field(..., description="CSV content with user emails/IDs")


class BulkEnrollmentResponse(BaseModel):
    """Response for bulk enrollment operation."""
    total_processed: int
    successful_enrollments: int
    failed_enrollments: int
    errors: List[str] = []
    enrolled_users: List[EnrollmentResponse] = []


class ClassStudentsResponse(BaseModel):
    """Response for listing class students."""
    class_id: str
    class_name: str
    total_students: int
    max_students: Optional[int]
    students: List[Dict[str, Any]] = []


class EnrollmentHistoryResponse(BaseModel):
    """Response for enrollment history."""
    user_id: str
    user_name: str
    class_id: str
    class_name: str
    enrollment_date: datetime
    unenrollment_date: Optional[datetime] = None
    status: str  # enrolled, unenrolled, completed
