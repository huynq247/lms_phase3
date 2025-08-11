"""
Multi-Level Enrollment Data Models for Phase 5.7
Comprehensive enrollment management across classes and courses
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from enum import Enum


class EnrollmentStatus(str, Enum):
    """Enrollment status options"""
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    SUSPENDED = "suspended"
    PENDING = "pending"
    WAITLISTED = "waitlisted"


class EnrollmentType(str, Enum):
    """Type of enrollment"""
    CLASS_BASED = "class_based"  # Enrolled through class
    INDIVIDUAL = "individual"    # Direct course enrollment
    BULK = "bulk"               # Bulk enrollment
    AUTO = "auto"               # Auto-enrollment


class ActivityType(str, Enum):
    """Types of learning activities"""
    LESSON_VIEW = "lesson_view"
    LESSON_COMPLETE = "lesson_complete"
    DECK_PRACTICE = "deck_practice"
    ASSIGNMENT_SUBMIT = "assignment_submit"
    QUIZ_ATTEMPT = "quiz_attempt"
    FORUM_POST = "forum_post"
    LOGIN = "login"
    DOWNLOAD = "download"


# Base Classes
class EnrollmentBase(BaseModel):
    """Base enrollment model with common fields"""
    student_id: str = Field(..., description="ID of enrolled student")
    enrollment_date: datetime = Field(default_factory=datetime.utcnow, description="Enrollment timestamp")
    status: EnrollmentStatus = Field(default=EnrollmentStatus.ACTIVE, description="Current enrollment status")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    last_activity_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    completion_date: Optional[datetime] = Field(None, description="Completion timestamp")
    enrolled_by: str = Field(..., description="User ID who created the enrollment")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('student_id', 'enrolled_by', pre=True)
    def convert_objectid_to_string(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }


# Class Enrollment Models
class ClassEnrollmentCreate(BaseModel):
    """Model for creating class enrollment"""
    class_id: str = Field(..., description="Class ID to enroll in")
    student_id: str = Field(..., description="Student ID to enroll")
    enrollment_type: EnrollmentType = Field(default=EnrollmentType.CLASS_BASED)
    auto_enroll_courses: bool = Field(default=True, description="Auto-enroll in class courses")
    notes: Optional[str] = Field(None, max_length=500, description="Enrollment notes")


class ClassEnrollmentUpdate(BaseModel):
    """Model for updating class enrollment"""
    status: Optional[EnrollmentStatus] = Field(None)
    notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(None)


class ClassEnrollmentResponse(EnrollmentBase):
    """Model for class enrollment response"""
    id: str = Field(..., description="Enrollment ID")
    class_id: str = Field(..., description="Class ID")
    class_title: Optional[str] = Field(None, description="Class title for display")
    class_description: Optional[str] = Field(None, description="Class description")
    enrollment_type: EnrollmentType = Field(..., description="Type of enrollment")
    courses_enrolled: List[str] = Field(default_factory=list, description="Auto-enrolled course IDs")
    total_courses: int = Field(default=0, description="Total courses in class")
    completed_courses: int = Field(default=0, description="Completed courses count")
    notes: Optional[str] = Field(None, description="Enrollment notes")
    is_active: bool = Field(True, description="Whether enrollment is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Course Enrollment Models
class CourseEnrollmentCreate(BaseModel):
    """Model for creating course enrollment"""
    course_id: str = Field(..., description="Course ID to enroll in")
    student_id: str = Field(..., description="Student ID to enroll")
    enrollment_type: EnrollmentType = Field(default=EnrollmentType.INDIVIDUAL)
    class_enrollment_id: Optional[str] = Field(None, description="Related class enrollment ID")
    prerequisites_check: bool = Field(default=True, description="Check prerequisites")
    notes: Optional[str] = Field(None, max_length=500, description="Enrollment notes")


class CourseEnrollmentUpdate(BaseModel):
    """Model for updating course enrollment"""
    status: Optional[EnrollmentStatus] = Field(None)
    notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(None)


class CourseEnrollmentResponse(EnrollmentBase):
    """Model for course enrollment response"""
    id: str = Field(..., description="Enrollment ID")
    course_id: str = Field(..., description="Course ID")
    course_title: Optional[str] = Field(None, description="Course title for display")
    course_description: Optional[str] = Field(None, description="Course description")
    enrollment_type: EnrollmentType = Field(..., description="Type of enrollment")
    class_enrollment_id: Optional[str] = Field(None, description="Related class enrollment")
    class_title: Optional[str] = Field(None, description="Class title if class-based")
    lessons_completed: int = Field(default=0, description="Number of lessons completed")
    total_lessons: int = Field(default=0, description="Total lessons in course")
    decks_practiced: int = Field(default=0, description="Number of decks practiced")
    total_decks: int = Field(default=0, description="Total decks assigned")
    time_spent_minutes: int = Field(default=0, description="Total time spent")
    notes: Optional[str] = Field(None, description="Enrollment notes")
    is_active: bool = Field(True, description="Whether enrollment is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Progress Tracking Models
class EnrollmentProgressCreate(BaseModel):
    """Model for creating progress entry"""
    enrollment_id: str = Field(..., description="Enrollment ID")
    enrollment_type: str = Field(..., pattern="^(class|course)$", description="Type of enrollment")
    lesson_id: Optional[str] = Field(None, description="Related lesson ID")
    deck_id: Optional[str] = Field(None, description="Related deck ID")
    activity_type: ActivityType = Field(..., description="Type of activity")
    progress_value: float = Field(0.0, ge=0.0, le=100.0, description="Progress increment")
    time_spent_minutes: int = Field(0, ge=0, description="Time spent on activity")
    score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Activity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Activity metadata")


class EnrollmentProgressResponse(BaseModel):
    """Model for progress response"""
    id: str = Field(..., description="Progress entry ID")
    enrollment_id: str = Field(..., description="Enrollment ID")
    enrollment_type: str = Field(..., description="Type of enrollment")
    student_id: str = Field(..., description="Student ID")
    lesson_id: Optional[str] = Field(None, description="Related lesson ID")
    lesson_title: Optional[str] = Field(None, description="Lesson title")
    deck_id: Optional[str] = Field(None, description="Related deck ID")
    deck_title: Optional[str] = Field(None, description="Deck title")
    activity_type: ActivityType = Field(..., description="Type of activity")
    progress_value: float = Field(..., description="Progress value")
    time_spent_minutes: int = Field(..., description="Time spent")
    score: Optional[float] = Field(None, description="Activity score")
    activity_date: datetime = Field(..., description="Activity timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Activity metadata")

    @validator('id', 'enrollment_id', 'student_id', 'lesson_id', 'deck_id', pre=True)
    def convert_objectid_to_string(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


# Enrollment Analytics Models
class EnrollmentStats(BaseModel):
    """Enrollment statistics model"""
    total_enrollments: int = 0
    active_enrollments: int = 0
    completed_enrollments: int = 0
    dropped_enrollments: int = 0
    suspended_enrollments: int = 0
    pending_enrollments: int = 0
    waitlisted_enrollments: int = 0
    average_progress: float = 0.0
    completion_rate: float = 0.0
    retention_rate: float = 0.0
    average_time_to_completion_days: float = 0.0


class ClassEnrollmentStats(EnrollmentStats):
    """Class-specific enrollment statistics"""
    class_id: str
    class_title: str
    total_courses: int = 0
    students_per_course_avg: float = 0.0
    most_popular_course_id: Optional[str] = None
    most_popular_course_title: Optional[str] = None


class CourseEnrollmentStats(EnrollmentStats):
    """Course-specific enrollment statistics"""
    course_id: str
    course_title: str
    total_lessons: int = 0
    average_lessons_completed: float = 0.0
    most_engaging_lesson_id: Optional[str] = None
    most_engaging_lesson_title: Optional[str] = None


class StudentEnrollmentOverview(BaseModel):
    """Student's enrollment overview"""
    student_id: str
    student_name: Optional[str] = None
    total_class_enrollments: int = 0
    total_course_enrollments: int = 0
    active_enrollments: int = 0
    completed_enrollments: int = 0
    overall_progress: float = 0.0
    total_time_spent_minutes: int = 0
    last_activity_at: Optional[datetime] = None
    class_enrollments: List[ClassEnrollmentResponse] = Field(default_factory=list)
    course_enrollments: List[CourseEnrollmentResponse] = Field(default_factory=list)


# Bulk Operations Models
class BulkEnrollmentCreate(BaseModel):
    """Model for bulk enrollment operations"""
    target_id: str = Field(..., description="Class or Course ID")
    target_type: str = Field(..., pattern="^(class|course)$", description="Target type")
    student_ids: List[str] = Field(..., min_items=1, max_items=100, description="Student IDs to enroll")
    enrollment_type: EnrollmentType = Field(default=EnrollmentType.BULK)
    auto_enroll_courses: bool = Field(default=True, description="Auto-enroll in courses (for class)")
    notes: Optional[str] = Field(None, max_length=500, description="Bulk enrollment notes")


class BulkEnrollmentResult(BaseModel):
    """Result of bulk enrollment operation"""
    successful_enrollments: int = 0
    failed_enrollments: int = 0
    total_attempted: int = 0
    successful_student_ids: List[str] = Field(default_factory=list)
    failed_enrollments_details: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class EnrollmentStatusUpdate(BaseModel):
    """Model for updating enrollment status"""
    status: EnrollmentStatus = Field(..., description="New status")
    reason: Optional[str] = Field(None, max_length=200, description="Reason for status change")
    effective_date: Optional[datetime] = Field(None, description="Effective date of change")
    notify_student: bool = Field(default=True, description="Send notification to student")


# Query and Filter Models
class EnrollmentFilter(BaseModel):
    """Filtering options for enrollment queries"""
    status: Optional[List[EnrollmentStatus]] = Field(None, description="Filter by status")
    enrollment_type: Optional[List[EnrollmentType]] = Field(None, description="Filter by enrollment type")
    date_from: Optional[datetime] = Field(None, description="Enrollment date from")
    date_to: Optional[datetime] = Field(None, description="Enrollment date to")
    progress_min: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum progress")
    progress_max: Optional[float] = Field(None, ge=0.0, le=100.0, description="Maximum progress")
    include_inactive: bool = Field(default=False, description="Include inactive enrollments")


class EnrollmentSearchQuery(BaseModel):
    """Search query for enrollments"""
    search_term: Optional[str] = Field(None, min_length=2, max_length=100, description="Search term")
    filters: Optional[EnrollmentFilter] = Field(None, description="Additional filters")
    sort_by: str = Field(default="enrollment_date", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")


# Response Models for Lists
class EnrollmentListResponse(BaseModel):
    """Paginated enrollment list response"""
    enrollments: List[Union[ClassEnrollmentResponse, CourseEnrollmentResponse]]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ProgressListResponse(BaseModel):
    """Paginated progress list response"""
    progress_entries: List[EnrollmentProgressResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
