"""
Enrollment Reporting Data Models for Phase 5.8
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReportType(str, Enum):
    """Types of reports"""
    CLASS_ENROLLMENT = "class_enrollment"
    COURSE_ENROLLMENT = "course_enrollment"
    STUDENT_PROGRESS = "student_progress"
    ACTIVITY_SUMMARY = "activity_summary"


class ExportFormat(str, Enum):
    """Export format options"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


# Base Report Models
class ReportMetadata(BaseModel):
    """Report metadata"""
    report_type: ReportType
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    total_records: int = 0
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class StudentEnrollmentData(BaseModel):
    """Student data in enrollment reports"""
    student_id: str
    student_name: str
    email: str
    enrollment_date: datetime
    status: str
    progress_percentage: float = 0.0
    last_activity_at: Optional[datetime] = None
    completion_date: Optional[datetime] = None


# Class Enrollment Report
class ClassEnrollmentReport(BaseModel):
    """Class enrollment report"""
    class_id: str
    class_name: str
    teacher_name: Optional[str] = None
    total_students: int = 0
    active_students: int = 0
    completed_students: int = 0
    average_progress: float = 0.0
    students: List[StudentEnrollmentData] = Field(default_factory=list)
    metadata: ReportMetadata


# Course Enrollment Report  
class CourseEnrollmentReport(BaseModel):
    """Course enrollment report"""
    course_id: str
    course_name: str
    total_students: int = 0  # Add this field
    active_students: int = 0  # Add this field
    total_enrollments: int = 0
    class_based_enrollments: int = 0
    individual_enrollments: int = 0
    average_completion_rate: float = 0.0  # Rename for consistency
    average_progress: float = 0.0
    enrollments: List[StudentEnrollmentData] = Field(default_factory=list)  # Rename from students
    metadata: ReportMetadata


# Student Progress Report
class LessonProgressData(BaseModel):
    """Lesson progress data"""
    lesson_id: str
    lesson_name: str
    status: str
    progress_percentage: float = 0.0
    time_spent_minutes: int = 0
    completed_at: Optional[datetime] = None


class StudentProgressReport(BaseModel):
    """Student progress report"""
    student_id: str
    student_name: str
    total_enrollments: int = 0
    active_enrollments: int = 0
    completed_enrollments: int = 0
    overall_progress: float = 0.0
    total_time_spent: int = 0
    lessons_progress: List[LessonProgressData] = Field(default_factory=list)
    class_enrollments: List[Dict[str, Any]] = Field(default_factory=list)
    course_enrollments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: ReportMetadata


# Activity Summary Report
class ActivityData(BaseModel):
    """Activity data"""
    activity_type: str
    count: int
    total_time_minutes: int = 0
    date: datetime


class ActivitySummaryReport(BaseModel):
    """Activity summary report"""
    period_start: datetime
    period_end: datetime
    total_activities: int = 0
    unique_students: int = 0
    total_time_spent: int = 0
    activities: List[ActivityData] = Field(default_factory=list)  # Add this field
    activities_by_type: List[ActivityData] = Field(default_factory=list)
    daily_activities: List[ActivityData] = Field(default_factory=list)
    top_active_students: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: ReportMetadata


# Export Models
class ReportExportRequest(BaseModel):
    """Report export request"""
    report_type: ReportType
    format: ExportFormat = ExportFormat.JSON
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = True


class ReportExportResponse(BaseModel):
    """Report export response"""
    download_url: Optional[str] = None
    file_name: str
    file_size_bytes: int = 0
    format: ExportFormat
    expires_at: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
