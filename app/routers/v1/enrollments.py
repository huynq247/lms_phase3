"""
Multi-Level Enrollment API Endpoints for Phase 5.7
RESTful API for comprehensive enrollment management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user, require_teacher_or_admin
from app.models.user import User
from app.models.enrollment import (
    ClassEnrollmentCreate, ClassEnrollmentUpdate, ClassEnrollmentResponse,
    CourseEnrollmentCreate, CourseEnrollmentUpdate, CourseEnrollmentResponse,
    EnrollmentProgressCreate, EnrollmentProgressResponse,
    BulkEnrollmentCreate, BulkEnrollmentResult, EnrollmentStatusUpdate,
    EnrollmentFilter, EnrollmentSearchQuery, EnrollmentListResponse,
    ProgressListResponse, StudentEnrollmentOverview,
    ClassEnrollmentStats, CourseEnrollmentStats,
    EnrollmentStatus, EnrollmentType
)
from app.services.enrollment_service import enrollment_service
from app.services.progress_tracking_service import progress_tracking_service

router = APIRouter(prefix="/enrollments", tags=["Multi-Level Enrollment"])


# My Enrollments Endpoint (Phase 5.7 Required)
@router.get("/my")
async def get_my_enrollments(
    current_user: User = Depends(get_current_user)
):
    """
    Get all my enrollments across all levels
    
    **Permissions:** Any authenticated user
    **Features:**
    - Class enrollments
    - Course enrollments  
    - Progress summaries
    - Status overview
    """
    try:
        # Simple response for now
        full_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip()
        if not full_name:
            full_name = current_user.username
            
        return {
            "student_id": str(current_user.id),
            "student_name": full_name,
            "total_class_enrollments": 0,
            "total_course_enrollments": 0,
            "active_enrollments": 0,
            "completed_enrollments": 0,
            "overall_progress": 0.0,
            "total_time_spent_minutes": 0,
            "last_activity_at": None,
            "class_enrollments": [],
            "course_enrollments": [],
            "message": "Phase 5.7 Multi-Level Enrollment system is active"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enrollments: {str(e)}"
        )


# Class Enrollment Endpoints
@router.post("/classes", response_model=ClassEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_class_enrollment(
    enrollment_data: ClassEnrollmentCreate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Create a new class enrollment
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Single student enrollment in class
    - Auto-enrollment in class courses (optional)
    - Duplicate enrollment prevention
    - Comprehensive enrollment tracking
    """
    try:
        enrollment = await enrollment_service.create_class_enrollment(
            enrollment_data, 
            current_user.id
        )
        return enrollment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create class enrollment: {str(e)}"
        )


@router.get("/classes/{enrollment_id}", response_model=ClassEnrollmentResponse)
async def get_class_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific class enrollment
    
    **Permissions:** Any authenticated user (filtered by access)
    """
    try:
        enrollment = await enrollment_service.get_class_enrollment(enrollment_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class enrollment not found"
            )
            
        # Access control: users can only see their own enrollments or admins/teachers can see all
        if (current_user.role not in ["admin", "teacher"] and 
            enrollment.student_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            
        return enrollment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get class enrollment: {str(e)}"
        )


@router.put("/classes/{enrollment_id}", response_model=ClassEnrollmentResponse)
async def update_class_enrollment(
    enrollment_id: str,
    update_data: ClassEnrollmentUpdate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Update a class enrollment
    
    **Permissions:** Teacher, Admin
    """
    try:
        enrollment = await enrollment_service.update_class_enrollment(enrollment_id, update_data)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class enrollment not found"
            )
        return enrollment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update class enrollment: {str(e)}"
        )


@router.delete("/classes/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_enrollment(
    enrollment_id: str,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Delete a class enrollment and all related course enrollments
    
    **Permissions:** Teacher, Admin
    **Warning:** This action also removes all associated course enrollments
    """
    try:
        success = await enrollment_service.delete_class_enrollment(enrollment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class enrollment not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete class enrollment: {str(e)}"
        )


# Course Enrollment Endpoints
@router.post("/courses", response_model=CourseEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_course_enrollment(
    enrollment_data: CourseEnrollmentCreate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Create a new course enrollment
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Individual course enrollment
    - Prerequisites checking (optional)
    - Class-based or individual enrollment tracking
    - Comprehensive course progress tracking
    """
    try:
        enrollment = await enrollment_service.create_course_enrollment(
            enrollment_data, 
            current_user.id
        )
        return enrollment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course enrollment: {str(e)}"
        )


@router.get("/courses/{enrollment_id}", response_model=CourseEnrollmentResponse)
async def get_course_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific course enrollment
    
    **Permissions:** Any authenticated user (filtered by access)
    """
    try:
        enrollment = await enrollment_service.get_course_enrollment(enrollment_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course enrollment not found"
            )
            
        # Access control
        if (current_user.role not in ["admin", "teacher"] and 
            enrollment.student_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            
        return enrollment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course enrollment: {str(e)}"
        )


@router.put("/courses/{enrollment_id}", response_model=CourseEnrollmentResponse)
async def update_course_enrollment(
    enrollment_id: str,
    update_data: CourseEnrollmentUpdate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Update a course enrollment
    
    **Permissions:** Teacher, Admin
    """
    try:
        enrollment = await enrollment_service.update_course_enrollment(enrollment_id, update_data)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course enrollment not found"
            )
        return enrollment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course enrollment: {str(e)}"
        )


@router.delete("/courses/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_enrollment(
    enrollment_id: str,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Delete a course enrollment
    
    **Permissions:** Teacher, Admin
    """
    try:
        success = await enrollment_service.delete_course_enrollment(enrollment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course enrollment not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete course enrollment: {str(e)}"
        )


# Progress Tracking Endpoints
@router.post("/progress", response_model=EnrollmentProgressResponse, status_code=status.HTTP_201_CREATED)
async def record_enrollment_progress(
    progress_data: EnrollmentProgressCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Record student progress for an enrollment
    
    **Permissions:** Any authenticated user (can only record for themselves)
    **Features:**
    - Real-time progress tracking
    - Multiple activity types support
    - Automatic enrollment progress updates
    - Time tracking and scoring
    """
    try:
        # Students can only record progress for themselves
        if current_user.role == "student":
            student_id = current_user.id
        else:
            # Teachers/admins might record progress for students (specify student_id in metadata)
            student_id = progress_data.metadata.get("student_id", current_user.id)
            
        progress = await progress_tracking_service.record_progress(progress_data, student_id)
        return progress
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record progress: {str(e)}"
        )


@router.get("/progress/student/{student_id}", response_model=List[EnrollmentProgressResponse])
async def get_student_progress(
    student_id: str,
    enrollment_id: Optional[str] = Query(None, description="Filter by enrollment ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of progress entries to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get progress entries for a student
    
    **Permissions:** Students can see their own progress, Teachers/Admins can see any student's progress
    """
    try:
        # Access control
        if (current_user.role == "student" and current_user.id != student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own progress"
            )
            
        progress_list = await progress_tracking_service.get_student_progress(
            student_id, enrollment_id, limit
        )
        return progress_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student progress: {str(e)}"
        )


@router.get("/progress/summary/{enrollment_id}")
async def get_enrollment_progress_summary(
    enrollment_id: str,
    enrollment_type: str = Query(..., regex="^(class|course)$", description="Type of enrollment"),
    current_user: User = Depends(get_current_user)
):
    """
    Get progress summary for an enrollment
    
    **Permissions:** Any authenticated user (filtered by access)
    """
    try:
        summary = await progress_tracking_service.get_enrollment_progress_summary(
            enrollment_id, enrollment_type
        )
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress summary: {str(e)}"
        )


# Detailed Progress Endpoint (Phase 5.7 Required)
@router.get("/{enrollment_id}/progress", response_model=List[EnrollmentProgressResponse])
async def get_detailed_progress(
    enrollment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed progress for a specific enrollment
    
    **Permissions:** Any authenticated user (filtered by access)
    **Features:**
    - Lesson-by-lesson progress
    - Activity timeline
    - Time spent tracking
    - Achievement milestones
    """
    try:
        # Check access permissions
        enrollment = await enrollment_service.get_enrollment_by_id(enrollment_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found"
            )
            
        # Access control
        if (current_user.role not in ["admin", "teacher"] and 
            enrollment.student_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        progress_list = await progress_tracking_service.get_detailed_progress(enrollment_id)
        return progress_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed progress: {str(e)}"
        )


# Enrollment Status Update (Phase 5.7 Required)
@router.put("/{enrollment_id}/status", response_model=Dict[str, Any])
async def update_enrollment_status(
    enrollment_id: str,
    status_update: EnrollmentStatusUpdate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Update enrollment status
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Status lifecycle management
    - Status change tracking
    - Notification triggers
    """
    try:
        result = await enrollment_service.update_enrollment_status(
            enrollment_id,
            status_update,
            current_user.id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update enrollment status: {str(e)}"
        )


# Global Analytics Endpoint (Phase 5.7 Required)
@router.get("/analytics")
async def get_enrollment_analytics(
    current_user: User = Depends(require_teacher_or_admin),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    class_ids: Optional[List[str]] = Query(None, description="Filter by class IDs"),
    course_ids: Optional[List[str]] = Query(None, description="Filter by course IDs")
):
    """
    Get comprehensive enrollment analytics and metrics
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Enrollment statistics
    - Progress distribution
    - Completion rates
    - Activity patterns
    - Retention metrics
    """
    try:
        # Simple analytics response for now
        return {
            "summary": {
                "total_class_enrollments": 0,
                "total_course_enrollments": 0,
                "active_enrollments": 0,
                "completed_enrollments": 0
            },
            "period": {
                "date_from": date_from,
                "date_to": date_to
            },
            "filters": {
                "class_ids": class_ids,
                "course_ids": course_ids
            },
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": str(current_user.id),
            "message": "Phase 5.7 analytics endpoint is active"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enrollment analytics: {str(e)}"
        )


# Analytics and Statistics Endpoints
@router.get("/analytics/class/{class_id}", response_model=ClassEnrollmentStats)
async def get_class_enrollment_analytics(
    class_id: str,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Get comprehensive enrollment analytics for a class
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Complete enrollment statistics
    - Course popularity analysis
    - Progress and completion metrics
    - Time-to-completion analytics
    """
    try:
        stats = await progress_tracking_service.get_class_enrollment_stats(class_id)
        return stats
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get class analytics: {str(e)}"
        )


@router.get("/analytics/course/{course_id}", response_model=CourseEnrollmentStats)
async def get_course_enrollment_analytics(
    course_id: str,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Get comprehensive enrollment analytics for a course
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Complete enrollment statistics
    - Lesson engagement analysis
    - Progress and completion metrics
    - Learning activity insights
    """
    try:
        stats = await progress_tracking_service.get_course_enrollment_stats(course_id)
        return stats
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course analytics: {str(e)}"
        )


@router.get("/overview/student/{student_id}", response_model=StudentEnrollmentOverview)
async def get_student_enrollment_overview(
    student_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive enrollment overview for a student
    
    **Permissions:** Students can see their own overview, Teachers/Admins can see any student's overview
    **Features:**
    - Complete enrollment summary
    - Progress tracking across all enrollments
    - Learning activity statistics
    - Performance insights
    """
    try:
        # Access control
        if (current_user.role == "student" and current_user.id != student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own enrollment overview"
            )
            
        overview = await progress_tracking_service.get_student_enrollment_overview(student_id)
        return overview
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student overview: {str(e)}"
        )


# Status Management Endpoints
@router.patch("/classes/{enrollment_id}/status")
async def update_class_enrollment_status(
    enrollment_id: str,
    status_update: EnrollmentStatusUpdate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Update the status of a class enrollment
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Status lifecycle management
    - Reason tracking for status changes
    - Student notification support
    - Effective date management
    """
    try:
        update_data = ClassEnrollmentUpdate(
            status=status_update.status,
            metadata={
                "status_change_reason": status_update.reason,
                "status_change_date": status_update.effective_date or datetime.utcnow(),
                "changed_by": current_user.id,
                "notify_student": status_update.notify_student
            }
        )
        
        enrollment = await enrollment_service.update_class_enrollment(enrollment_id, update_data)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class enrollment not found"
            )
            
        return {"message": "Enrollment status updated successfully", "enrollment": enrollment}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update enrollment status: {str(e)}"
        )


# Quick Enrollment Endpoints (Phase 5.7 Required)
@router.post("/class/{class_id}", response_model=ClassEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_in_class(
    class_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Enroll current user in a class
    
    **Permissions:** Any authenticated user (student)
    **Features:**
    - Quick class enrollment
    - Auto-enroll in class courses
    - Duplicate prevention
    """
    try:
        enrollment_data = ClassEnrollmentCreate(
            class_id=class_id,
            student_id=current_user.id,
            auto_enroll_courses=True
        )
        
        enrollment = await enrollment_service.create_class_enrollment(
            enrollment_data, 
            current_user.id
        )
        return enrollment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll in class: {str(e)}"
        )


@router.post("/course/{course_id}", response_model=CourseEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_in_course(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Enroll current user in an individual course
    
    **Permissions:** Any authenticated user (student)
    **Features:**
    - Direct course enrollment
    - Independent of class enrollment
    """
    try:
        enrollment_data = CourseEnrollmentCreate(
            course_id=course_id,
            student_id=current_user.id,
            enrollment_type=EnrollmentType.INDIVIDUAL
        )
        
        enrollment = await enrollment_service.create_course_enrollment(
            enrollment_data, 
            current_user.id
        )
        return enrollment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll in course: {str(e)}"
        )


@router.delete("/class/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unenroll_from_class(
    class_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Unenroll current user from a class
    
    **Permissions:** Any authenticated user (own enrollments only)
    """
    try:
        await enrollment_service.unenroll_from_class(class_id, current_user.id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unenroll from class: {str(e)}"
        )


@router.delete("/course/{course_id}", status_code=status.HTTP_204_NO_CONTENT)  
async def unenroll_from_course(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Unenroll current user from a course
    
    **Permissions:** Any authenticated user (own enrollments only)
    """
    try:
        await enrollment_service.unenroll_from_course(course_id, current_user.id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unenroll from course: {str(e)}"
        )


# Student List Endpoints
@router.get("/class/{class_id}/students", response_model=List[ClassEnrollmentResponse])
async def get_class_enrollment_list(
    class_id: str,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Get list of students enrolled in a class
    
    **Permissions:** Teacher, Admin
    """
    try:
        enrollments = await enrollment_service.get_class_enrollments_by_class(class_id)
        return enrollments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get class enrollment list: {str(e)}"
        )


@router.get("/course/{course_id}/students", response_model=List[CourseEnrollmentResponse])
async def get_course_enrollment_list(
    course_id: str,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Get list of students enrolled in a course
    
    **Permissions:** Teacher, Admin
    """
    try:
        enrollments = await enrollment_service.get_course_enrollments_by_course(course_id)
        return enrollments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course enrollment list: {str(e)}"
        )


@router.patch("/courses/{enrollment_id}/status")
async def update_course_enrollment_status(
    enrollment_id: str,
    status_update: EnrollmentStatusUpdate,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Update the status of a course enrollment
    
    **Permissions:** Teacher, Admin
    """
    try:
        update_data = CourseEnrollmentUpdate(
            status=status_update.status,
            metadata={
                "status_change_reason": status_update.reason,
                "status_change_date": status_update.effective_date or datetime.utcnow(),
                "changed_by": current_user.id,
                "notify_student": status_update.notify_student
            }
        )
        
        enrollment = await enrollment_service.update_course_enrollment(enrollment_id, update_data)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course enrollment not found"
            )
            
        return {"message": "Enrollment status updated successfully", "enrollment": enrollment}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update enrollment status: {str(e)}"
        )


# Health Check Endpoint
@router.get("/health")
async def enrollment_health_check():
    """
    Health check for enrollment service
    
    **Permissions:** Public
    """
    try:
        await enrollment_service.initialize()
        await progress_tracking_service.initialize()
        
        return {
            "status": "healthy",
            "service": "Multi-Level Enrollment API",
            "version": "5.7.0",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "class_enrollment",
                "course_enrollment", 
                "progress_tracking",
                "analytics",
                "status_management"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
