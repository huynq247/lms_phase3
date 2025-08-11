"""
Enrollment Reporting Service for Phase 5.8
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging

from app.core.deps import get_database
from app.models.reports import (
    ClassEnrollmentReport, CourseEnrollmentReport, StudentProgressReport,
    ActivitySummaryReport, ReportMetadata, StudentEnrollmentData,
    LessonProgressData, ActivityData, ReportType, ReportExportRequest,
    ReportExportResponse, ExportFormat
)

logger = logging.getLogger(__name__)


class ReportingService:
    """Service for generating enrollment reports"""

    def __init__(self):
        self.db = None

    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()

    # Class Enrollment Reports
    async def generate_class_enrollment_report(
        self,
        class_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        generated_by: str = None
    ) -> ClassEnrollmentReport:
        """Generate class enrollment report"""
        await self.initialize()
        
        try:
            # Build query filters
            query = {"class_id": class_id}
            if date_from and date_to:
                query["enrollment_date"] = {"$gte": date_from, "$lte": date_to}
            
            # Get class info (mock for now)
            class_name = f"Class {class_id}"
            teacher_name = "Teacher Name"
            
            # Get enrollments
            enrollments = await self.db.class_enrollments.find(query).to_list(length=None)
            
            # Process student data
            students = []
            active_count = 0
            completed_count = 0
            total_progress = 0.0
            
            for enrollment in enrollments:
                student_data = StudentEnrollmentData(
                    student_id=enrollment["student_id"],
                    student_name=f"Student {enrollment['student_id'][:8]}",
                    email=f"student{enrollment['student_id'][:8]}@example.com",
                    enrollment_date=enrollment["enrollment_date"],
                    status=enrollment.get("status", "active"),
                    progress_percentage=enrollment.get("progress_percentage", 0.0),
                    last_activity_at=enrollment.get("last_activity_at"),
                    completion_date=enrollment.get("completion_date")
                )
                students.append(student_data)
                
                if enrollment.get("status") == "active":
                    active_count += 1
                elif enrollment.get("status") == "completed":
                    completed_count += 1
                
                total_progress += enrollment.get("progress_percentage", 0.0)
            
            average_progress = total_progress / len(enrollments) if enrollments else 0.0
            
            # Create metadata
            metadata = ReportMetadata(
                report_type=ReportType.CLASS_ENROLLMENT,
                generated_by=generated_by or "system",
                date_from=date_from,
                date_to=date_to,
                total_records=len(enrollments),
                filters_applied={"class_id": class_id}
            )
            
            return ClassEnrollmentReport(
                class_id=class_id,
                class_name=class_name,
                teacher_name=teacher_name,
                total_students=len(enrollments),
                active_students=active_count,
                completed_students=completed_count,
                average_progress=average_progress,
                students=students,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating class enrollment report: {str(e)}")
            raise

    # Course Enrollment Reports
    async def generate_course_enrollment_report(
        self,
        course_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        generated_by: str = None
    ) -> CourseEnrollmentReport:
        """Generate course enrollment report"""
        await self.initialize()
        
        try:
            # Build query filters
            query = {"course_id": course_id}
            if date_from and date_to:
                query["enrollment_date"] = {"$gte": date_from, "$lte": date_to}
            
            # Get course info (mock for now)
            course_name = f"Course {course_id}"
            
            # Get enrollments
            enrollments = await self.db.course_enrollments.find(query).to_list(length=None)
            
            # Process enrollment data
            students = []
            class_based_count = 0
            individual_count = 0
            total_progress = 0.0
            completed_count = 0
            
            for enrollment in enrollments:
                student_data = StudentEnrollmentData(
                    student_id=enrollment["student_id"],
                    student_name=f"Student {enrollment['student_id'][:8]}",
                    email=f"student{enrollment['student_id'][:8]}@example.com",
                    enrollment_date=enrollment["enrollment_date"],
                    status=enrollment.get("status", "active"),
                    progress_percentage=enrollment.get("progress_percentage", 0.0),
                    last_activity_at=enrollment.get("last_activity_at"),
                    completion_date=enrollment.get("completion_date")
                )
                students.append(student_data)
                
                # Count enrollment types
                if enrollment.get("enrollment_type") == "class_based":
                    class_based_count += 1
                else:
                    individual_count += 1
                
                # Calculate metrics
                total_progress += enrollment.get("progress_percentage", 0.0)
                if enrollment.get("status") == "completed":
                    completed_count += 1
            
            average_progress = total_progress / len(enrollments) if enrollments else 0.0
            completion_rate = (completed_count / len(enrollments) * 100) if enrollments else 0.0
            
            # Create metadata
            metadata = ReportMetadata(
                report_type=ReportType.COURSE_ENROLLMENT,
                generated_by=generated_by or "system",
                date_from=date_from,
                date_to=date_to,
                total_records=len(enrollments),
                filters_applied={"course_id": course_id}
            )
            
            return CourseEnrollmentReport(
                course_id=course_id,
                course_name=course_name,
                total_students=len(enrollments),  # Add this field
                active_students=len(enrollments) - completed_count,  # Add this field
                total_enrollments=len(enrollments),
                class_based_enrollments=class_based_count,
                individual_enrollments=individual_count,
                average_completion_rate=completion_rate,  # Use new field name
                average_progress=average_progress,
                enrollments=students,  # Use new field name
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating course enrollment report: {str(e)}")
            raise

    # Student Progress Reports
    async def generate_student_progress_report(
        self,
        student_id: str,
        generated_by: str = None
    ) -> StudentProgressReport:
        """Generate student progress report"""
        await self.initialize()
        
        try:
            # Get student enrollments
            class_enrollments = await self.db.class_enrollments.find(
                {"student_id": student_id}
            ).to_list(length=None)
            
            course_enrollments = await self.db.course_enrollments.find(
                {"student_id": student_id}
            ).to_list(length=None)
            
            # Calculate metrics
            total_enrollments = len(class_enrollments) + len(course_enrollments)
            active_enrollments = 0
            completed_enrollments = 0
            total_progress = 0.0
            
            # Process class enrollments
            class_data = []
            for enrollment in class_enrollments:
                class_data.append({
                    "class_id": enrollment["class_id"],
                    "status": enrollment.get("status", "active"),
                    "progress": enrollment.get("progress_percentage", 0.0),
                    "enrollment_date": enrollment["enrollment_date"]
                })
                
                if enrollment.get("status") == "active":
                    active_enrollments += 1
                elif enrollment.get("status") == "completed":
                    completed_enrollments += 1
                
                total_progress += enrollment.get("progress_percentage", 0.0)
            
            # Process course enrollments
            course_data = []
            for enrollment in course_enrollments:
                course_data.append({
                    "course_id": enrollment["course_id"],
                    "status": enrollment.get("status", "active"),
                    "progress": enrollment.get("progress_percentage", 0.0),
                    "enrollment_date": enrollment["enrollment_date"]
                })
                
                if enrollment.get("status") == "active":
                    active_enrollments += 1
                elif enrollment.get("status") == "completed":
                    completed_enrollments += 1
                
                total_progress += enrollment.get("progress_percentage", 0.0)
            
            overall_progress = total_progress / total_enrollments if total_enrollments else 0.0
            
            # Mock lesson progress data
            lessons_progress = [
                LessonProgressData(
                    lesson_id=f"lesson_{i}",
                    lesson_name=f"Lesson {i}",
                    status="completed" if i <= 3 else "active",
                    progress_percentage=100.0 if i <= 3 else 50.0,
                    time_spent_minutes=30,
                    completed_at=datetime.utcnow() - timedelta(days=i) if i <= 3 else None
                ) for i in range(1, 6)
            ]
            
            # Create metadata
            metadata = ReportMetadata(
                report_type=ReportType.STUDENT_PROGRESS,
                generated_by=generated_by or "system",
                total_records=total_enrollments,
                filters_applied={"student_id": student_id}
            )
            
            return StudentProgressReport(
                student_id=student_id,
                student_name=f"Student {student_id[:8]}",
                total_enrollments=total_enrollments,
                active_enrollments=active_enrollments,
                completed_enrollments=completed_enrollments,
                overall_progress=overall_progress,
                total_time_spent=150,  # Mock data
                lessons_progress=lessons_progress,
                class_enrollments=class_data,
                course_enrollments=course_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating student progress report: {str(e)}")
            raise

    # Activity Summary Reports
    async def generate_activity_summary_report(
        self,
        date_from: datetime,
        date_to: datetime,
        generated_by: str = None
    ) -> ActivitySummaryReport:
        """Generate activity summary report"""
        await self.initialize()
        
        try:
            # Mock activity data for demonstration
            activities_by_type = [
                ActivityData(
                    activity_type="lesson_view",
                    count=150,
                    total_time_minutes=300,
                    date=datetime.utcnow()
                ),
                ActivityData(
                    activity_type="deck_practice", 
                    count=89,
                    total_time_minutes=178,
                    date=datetime.utcnow()
                ),
                ActivityData(
                    activity_type="assignment_submit",
                    count=45,
                    total_time_minutes=90,
                    date=datetime.utcnow()
                )
            ]
            
            # Mock daily activities
            daily_activities = []
            for i in range(7):
                date = date_from + timedelta(days=i)
                if date <= date_to:
                    daily_activities.append(
                        ActivityData(
                            activity_type="daily_total",
                            count=20 + i * 5,
                            total_time_minutes=40 + i * 10,
                            date=date
                        )
                    )
            
            # Mock top active students
            top_students = [
                {"student_id": "student_1", "student_name": "Top Student 1", "activity_count": 45},
                {"student_id": "student_2", "student_name": "Top Student 2", "activity_count": 38},
                {"student_id": "student_3", "student_name": "Top Student 3", "activity_count": 32}
            ]
            
            total_activities = sum(activity.count for activity in activities_by_type)
            total_time = sum(activity.total_time_minutes for activity in activities_by_type)
            
            # Create metadata
            metadata = ReportMetadata(
                report_type=ReportType.ACTIVITY_SUMMARY,
                generated_by=generated_by or "system",
                date_from=date_from,
                date_to=date_to,
                total_records=total_activities,
                filters_applied={"period": f"{date_from} to {date_to}"}
            )
            
            return ActivitySummaryReport(
                period_start=date_from,
                period_end=date_to,
                total_activities=total_activities,
                unique_students=15,  # Mock data
                total_time_spent=total_time,
                activities=activities_by_type,  # Add this field
                activities_by_type=activities_by_type,
                daily_activities=daily_activities,
                top_active_students=top_students,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating activity summary report: {str(e)}")
            raise

    # Export functionality
    async def export_report_data(
        self,
        export_request: ReportExportRequest,
        generated_by: str = None
    ) -> ReportExportResponse:
        """Export report data in requested format"""
        try:
            # Mock export functionality
            file_name = f"report_{export_request.report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export_request.format}"
            
            return ReportExportResponse(
                download_url=f"/downloads/{file_name}",
                file_name=file_name,
                file_size_bytes=1024,  # Mock size
                format=export_request.format,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
        except Exception as e:
            logger.error(f"Error exporting report data: {str(e)}")
            raise


# Create service instance
reporting_service = ReportingService()
