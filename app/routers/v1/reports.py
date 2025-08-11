"""
Enrollment Reporting API Endpoints for Phase 5.8
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user, require_teacher_or_admin
from app.models.user import User
from app.models.reports import (
    ClassEnrollmentReport, CourseEnrollmentReport, StudentProgressReport,
    ActivitySummaryReport, ReportExportRequest, ReportExportResponse
)
from app.services.reporting_service import reporting_service

router = APIRouter(prefix="/reports", tags=["Enrollment Reporting"])


@router.get("/enrollment/class/{class_id}", response_model=ClassEnrollmentReport)
async def get_class_enrollment_report(
    class_id: str,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Generate class enrollment report
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Student enrollment list
    - Progress statistics
    - Activity status
    - Date range filtering
    """
    try:
        # Parse dates if provided
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
            
        report = await reporting_service.generate_class_enrollment_report(
            class_id=class_id,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            generated_by=str(current_user.id)
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate class enrollment report: {str(e)}"
        )


@router.get("/enrollment/course/{course_id}", response_model=CourseEnrollmentReport)
async def get_course_enrollment_report(
    course_id: str,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Generate course enrollment report
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Enrollment statistics
    - Completion rates
    - Student breakdown
    - Progress analytics
    """
    try:
        # Parse dates if provided
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
            
        report = await reporting_service.generate_course_enrollment_report(
            course_id=course_id,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            generated_by=str(current_user.id)
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate course enrollment report: {str(e)}"
        )


@router.get("/progress/student/{student_id}", response_model=StudentProgressReport)
async def get_student_progress_report(
    student_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Generate student progress report
    
    **Permissions:** Any authenticated user (filtered by access)
    **Features:**
    - Individual progress tracking
    - Lesson completion status
    - Time spent analytics
    - Enrollment overview
    """
    try:
        # Access control: users can only see their own reports or admins/teachers can see all
        if (current_user.role not in ["admin", "teacher"] and 
            str(current_user.id) != student_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            
        report = await reporting_service.generate_student_progress_report(
            student_id=student_id,
            generated_by=str(current_user.id)
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate student progress report: {str(e)}"
        )


@router.get("/activity/summary", response_model=ActivitySummaryReport)
async def get_activity_summary_report(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Generate activity summary report
    
    **Permissions:** Teacher, Admin
    **Features:**
    - Activity statistics
    - Learning patterns
    - Top active students
    - Daily activity trends
    """
    try:
        # Parse required dates
        parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
        
        # Validate date range
        if parsed_date_to < parsed_date_from:
            raise ValueError("End date must be after start date")
            
        if (parsed_date_to - parsed_date_from).days > 90:
            raise ValueError("Date range cannot exceed 90 days")
            
        report = await reporting_service.generate_activity_summary_report(
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            generated_by=str(current_user.id)
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate activity summary report: {str(e)}"
        )


@router.post("/enrollment/export", response_model=ReportExportResponse)
async def export_enrollment_data(
    export_request: ReportExportRequest,
    current_user: User = Depends(require_teacher_or_admin)
):
    """
    Export enrollment data in requested format
    
    **Permissions:** Teacher, Admin
    **Features:**
    - CSV and Excel export
    - Custom date ranges
    - Filtered data export
    - Download links
    """
    try:
        export_response = await reporting_service.export_report_data(
            export_request=export_request,
            generated_by=str(current_user.id)
        )
        
        return export_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export enrollment data: {str(e)}"
        )


@router.get("/health")
async def reports_health_check():
    """
    Health check for reporting service
    
    **Permissions:** Public
    """
    try:
        await reporting_service.initialize()
        
        return {
            "status": "healthy",
            "service": "Enrollment Reporting API",
            "version": "5.8.0",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "class_reports",
                "course_reports",
                "progress_tracking",
                "activity_analytics",
                "data_export"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
