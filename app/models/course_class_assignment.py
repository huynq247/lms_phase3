"""Course-Class Assignment models for Phase 5.4"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class CourseClassAssignmentBase(BaseModel):
    """Base model for course-class assignment."""
    class_id: str = Field(..., description="Class ID")
    course_id: str = Field(..., description="Course ID") 
    assigned_by: str = Field(..., description="User ID who made the assignment")
    assignment_notes: Optional[str] = Field(None, max_length=500, description="Optional notes about assignment")

class CourseClassAssignmentCreate(CourseClassAssignmentBase):
    """Request model for creating course-class assignment."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "class_id": "64a1b2c3d4e5f6789abcdef0",
                "course_id": "64a1b2c3d4e5f6789abcdef1", 
                "assigned_by": "64a1b2c3d4e5f6789abcdef2",
                "assignment_notes": "Assigned for semester 1"
            }
        }

class CourseClassAssignmentUpdate(BaseModel):
    """Request model for updating course-class assignment."""
    assignment_notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class CourseClassAssignmentResponse(CourseClassAssignmentBase):
    """Response model for course-class assignment."""
    id: str = Field(..., alias="_id")
    assigned_at: datetime
    is_active: bool = Field(default=True)
    
    # Extended info (populated from related collections)
    class_name: Optional[str] = Field(None, description="Name of the class")
    course_title: Optional[str] = Field(None, description="Title of the course")
    assigned_by_username: Optional[str] = Field(None, description="Username who made assignment")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": "64a1b2c3d4e5f6789abcdef3",
                "class_id": "64a1b2c3d4e5f6789abcdef0",
                "course_id": "64a1b2c3d4e5f6789abcdef1",
                "assigned_by": "64a1b2c3d4e5f6789abcdef2",
                "assigned_at": "2025-08-11T14:30:00.000Z",
                "is_active": True,
                "assignment_notes": "Assigned for semester 1",
                "class_name": "Web Development 101",
                "course_title": "Introduction to HTML/CSS",
                "assigned_by_username": "teacher_john"
            }
        }

class ClassCoursesResponse(BaseModel):
    """Response model for courses assigned to a class."""
    class_id: str
    class_name: str
    courses: List[CourseClassAssignmentResponse]
    total_courses: int
    
class CourseClassesResponse(BaseModel):
    """Response model for classes that have a course assigned."""
    course_id: str
    course_title: str  
    classes: List[CourseClassAssignmentResponse]
    total_classes: int

class BulkAssignmentRequest(BaseModel):
    """Request model for bulk course assignment."""
    course_id: str = Field(..., description="Course ID to assign")
    class_ids: List[str] = Field(..., min_items=1, description="List of class IDs to assign course to")
    assignment_notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "course_id": "64a1b2c3d4e5f6789abcdef1",
                "class_ids": ["64a1b2c3d4e5f6789abcdef0", "64a1b2c3d4e5f6789abcdef4"],
                "assignment_notes": "Bulk assignment for new semester"
            }
        }

class BulkAssignmentResponse(BaseModel):
    """Response model for bulk assignment results."""
    successful_assignments: List[CourseClassAssignmentResponse]
    failed_assignments: List[dict]  # {class_id, error_message}
    total_requested: int
    total_successful: int
    total_failed: int

class AssignmentStatsResponse(BaseModel):
    """Response model for assignment statistics."""
    total_assignments: int
    active_assignments: int
    inactive_assignments: int
    unique_courses: int
    unique_classes: int
    top_assigned_courses: List[dict]  # {course_id, course_title, assignment_count}
    top_classes_with_courses: List[dict]  # {class_id, class_name, course_count}
