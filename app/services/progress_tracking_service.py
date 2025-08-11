"""
Progress Tracking Service for Phase 5.7
Real-time progress tracking and analytics for enrollments
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from pymongo import UpdateOne, DESCENDING
import logging
from collections import defaultdict

from app.core.deps import get_database
from app.models.enrollment import (
    EnrollmentProgressCreate, EnrollmentProgressResponse,
    EnrollmentStats, ClassEnrollmentStats, CourseEnrollmentStats,
    StudentEnrollmentOverview, EnrollmentFilter, EnrollmentSearchQuery,
    ProgressListResponse, EnrollmentStatus, ActivityType
)

logger = logging.getLogger(__name__)


class ProgressTrackingService:
    """Service for tracking and analyzing enrollment progress"""

    def __init__(self):
        self.db = None

    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()

    # Progress Entry Management
    async def record_progress(
        self, 
        progress_data: EnrollmentProgressCreate, 
        student_id: str
    ) -> EnrollmentProgressResponse:
        """Record a new progress entry"""
        await self.initialize()
        
        try:
            # Verify enrollment exists
            enrollment_collection = (
                self.db.class_enrollments if progress_data.enrollment_type == "class"
                else self.db.course_enrollments
            )
            
            enrollment = await enrollment_collection.find_one({
                "_id": ObjectId(progress_data.enrollment_id),
                "student_id": student_id,
                "status": {"$in": [EnrollmentStatus.ACTIVE, EnrollmentStatus.PENDING]}
            })
            
            if not enrollment:
                raise ValueError(f"Active enrollment {progress_data.enrollment_id} not found for student")

            # Prepare progress document
            now = datetime.utcnow()
            progress_doc = {
                "_id": ObjectId(),
                "enrollment_id": progress_data.enrollment_id,
                "enrollment_type": progress_data.enrollment_type,
                "student_id": student_id,
                "lesson_id": progress_data.lesson_id,
                "deck_id": progress_data.deck_id,
                "activity_type": progress_data.activity_type,
                "progress_value": progress_data.progress_value,
                "time_spent_minutes": progress_data.time_spent_minutes,
                "score": progress_data.score,
                "activity_date": now,
                "metadata": progress_data.metadata
            }

            # Insert progress entry
            await self.db.enrollment_progress.insert_one(progress_doc)

            # Update enrollment progress asynchronously
            await self._update_enrollment_progress(
                progress_data.enrollment_id, 
                progress_data.enrollment_type,
                progress_data.activity_type,
                progress_data.progress_value,
                progress_data.time_spent_minutes
            )

            # Get additional data for response
            lesson_title = None
            deck_title = None
            
            if progress_data.lesson_id:
                lesson = await self.db.lessons.find_one({"_id": ObjectId(progress_data.lesson_id)})
                lesson_title = lesson.get("title") if lesson else None
                
            if progress_data.deck_id:
                deck = await self.db.decks.find_one({"_id": ObjectId(progress_data.deck_id)})
                deck_title = deck.get("title") if deck else None

            # Prepare response
            response_data = {
                **progress_doc,
                "id": str(progress_doc["_id"]),
                "lesson_title": lesson_title,
                "deck_title": deck_title
            }
            response_data.pop("_id")

            logger.info(f"Recorded progress for enrollment {progress_data.enrollment_id}")
            return EnrollmentProgressResponse(**response_data)

        except Exception as e:
            logger.error(f"Error recording progress: {str(e)}")
            raise

    async def get_student_progress(
        self, 
        student_id: str, 
        enrollment_id: Optional[str] = None,
        limit: int = 50
    ) -> List[EnrollmentProgressResponse]:
        """Get progress entries for a student"""
        await self.initialize()
        
        try:
            query = {"student_id": student_id}
            if enrollment_id:
                query["enrollment_id"] = enrollment_id

            progress_entries = await self.db.enrollment_progress.find(
                query
            ).sort("activity_date", DESCENDING).limit(limit).to_list(length=None)

            # Enrich with lesson and deck titles
            response_list = []
            for entry in progress_entries:
                lesson_title = None
                deck_title = None
                
                if entry.get("lesson_id"):
                    lesson = await self.db.lessons.find_one({"_id": ObjectId(entry["lesson_id"])})
                    lesson_title = lesson.get("title") if lesson else None
                    
                if entry.get("deck_id"):
                    deck = await self.db.decks.find_one({"_id": ObjectId(entry["deck_id"])})
                    deck_title = deck.get("title") if deck else None

                response_data = {
                    **entry,
                    "id": str(entry["_id"]),
                    "lesson_title": lesson_title,
                    "deck_title": deck_title
                }
                response_data.pop("_id")
                
                response_list.append(EnrollmentProgressResponse(**response_data))

            logger.info(f"Retrieved {len(response_list)} progress entries for student {student_id}")
            return response_list

        except Exception as e:
            logger.error(f"Error getting student progress: {str(e)}")
            raise

    async def get_enrollment_progress_summary(
        self, 
        enrollment_id: str, 
        enrollment_type: str
    ) -> Dict[str, Any]:
        """Get progress summary for an enrollment"""
        await self.initialize()
        
        try:
            # Aggregate progress data
            pipeline = [
                {"$match": {
                    "enrollment_id": enrollment_id,
                    "enrollment_type": enrollment_type
                }},
                {"$group": {
                    "_id": None,
                    "total_activities": {"$sum": 1},
                    "total_progress": {"$sum": "$progress_value"},
                    "total_time_minutes": {"$sum": "$time_spent_minutes"},
                    "average_score": {"$avg": "$score"},
                    "last_activity": {"$max": "$activity_date"},
                    "activity_types": {"$addToSet": "$activity_type"}
                }}
            ]

            result = await self.db.enrollment_progress.aggregate(pipeline).to_list(length=1)
            
            if not result:
                return {
                    "total_activities": 0,
                    "total_progress": 0.0,
                    "total_time_minutes": 0,
                    "average_score": None,
                    "last_activity": None,
                    "activity_types": []
                }

            summary = result[0]
            summary.pop("_id")
            
            # Get activity breakdown
            activity_breakdown = await self._get_activity_breakdown(enrollment_id, enrollment_type)
            summary["activity_breakdown"] = activity_breakdown

            logger.info(f"Generated progress summary for enrollment {enrollment_id}")
            return summary

        except Exception as e:
            logger.error(f"Error getting progress summary: {str(e)}")
            raise

    # Analytics Methods
    async def get_class_enrollment_stats(self, class_id: str) -> ClassEnrollmentStats:
        """Get enrollment statistics for a class"""
        await self.initialize()
        
        try:
            # Get class info
            class_info = await self.db.classes.find_one({"_id": ObjectId(class_id)})
            if not class_info:
                raise ValueError(f"Class {class_id} not found")

            # Basic enrollment stats
            enrollments = await self.db.class_enrollments.find({"class_id": class_id}).to_list(length=None)
            
            stats = self._calculate_basic_stats(enrollments)
            
            # Class-specific stats
            total_courses = len(class_info.get("course_ids", []))
            
            # Calculate students per course average
            if total_courses > 0:
                course_enrollments = await self.db.course_enrollments.count_documents({
                    "course_id": {"$in": class_info.get("course_ids", [])}
                })
                students_per_course_avg = course_enrollments / total_courses if total_courses > 0 else 0
            else:
                students_per_course_avg = 0

            # Find most popular course
            most_popular_course_id = None
            most_popular_course_title = None
            
            if class_info.get("course_ids"):
                popular_course = await self.db.course_enrollments.aggregate([
                    {"$match": {"course_id": {"$in": class_info["course_ids"]}}},
                    {"$group": {"_id": "$course_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 1}
                ]).to_list(length=1)
                
                if popular_course:
                    most_popular_course_id = popular_course[0]["_id"]
                    course_info = await self.db.courses.find_one({"_id": ObjectId(most_popular_course_id)})
                    most_popular_course_title = course_info.get("title") if course_info else None

            return ClassEnrollmentStats(
                class_id=class_id,
                class_title=class_info.get("title", "Unknown Class"),
                total_courses=total_courses,
                students_per_course_avg=students_per_course_avg,
                most_popular_course_id=most_popular_course_id,
                most_popular_course_title=most_popular_course_title,
                **stats
            )

        except Exception as e:
            logger.error(f"Error getting class enrollment stats: {str(e)}")
            raise

    async def get_course_enrollment_stats(self, course_id: str) -> CourseEnrollmentStats:
        """Get enrollment statistics for a course"""
        await self.initialize()
        
        try:
            # Get course info
            course_info = await self.db.courses.find_one({"_id": ObjectId(course_id)})
            if not course_info:
                raise ValueError(f"Course {course_id} not found")

            # Basic enrollment stats
            enrollments = await self.db.course_enrollments.find({"course_id": course_id}).to_list(length=None)
            
            stats = self._calculate_basic_stats(enrollments)
            
            # Course-specific stats
            total_lessons = await self.db.lessons.count_documents({"course_id": course_id})
            
            # Calculate average lessons completed
            if enrollments:
                avg_lessons = sum(e.get("lessons_completed", 0) for e in enrollments) / len(enrollments)
            else:
                avg_lessons = 0

            # Find most engaging lesson (most progress entries)
            most_engaging_lesson_id = None
            most_engaging_lesson_title = None
            
            lesson_ids = await self.db.lessons.distinct("_id", {"course_id": course_id})
            if lesson_ids:
                engaging_lesson = await self.db.enrollment_progress.aggregate([
                    {"$match": {
                        "lesson_id": {"$in": [str(lid) for lid in lesson_ids]},
                        "enrollment_type": "course"
                    }},
                    {"$group": {"_id": "$lesson_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 1}
                ]).to_list(length=1)
                
                if engaging_lesson:
                    most_engaging_lesson_id = engaging_lesson[0]["_id"]
                    lesson_info = await self.db.lessons.find_one({"_id": ObjectId(most_engaging_lesson_id)})
                    most_engaging_lesson_title = lesson_info.get("title") if lesson_info else None

            return CourseEnrollmentStats(
                course_id=course_id,
                course_title=course_info.get("title", "Unknown Course"),
                total_lessons=total_lessons,
                average_lessons_completed=avg_lessons,
                most_engaging_lesson_id=most_engaging_lesson_id,
                most_engaging_lesson_title=most_engaging_lesson_title,
                **stats
            )

        except Exception as e:
            logger.error(f"Error getting course enrollment stats: {str(e)}")
            raise

    async def get_student_enrollment_overview(self, student_id: str) -> StudentEnrollmentOverview:
        """Get comprehensive enrollment overview for a student"""
        await self.initialize()
        
        try:
            # Get student info
            student_info = await self.db.users.find_one({"_id": ObjectId(student_id)})
            student_name = None
            if student_info:
                profile = student_info.get("profile", {})
                student_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

            # Get class enrollments
            class_enrollments = await self.db.class_enrollments.find(
                {"student_id": student_id}
            ).to_list(length=None)
            
            # Get course enrollments
            course_enrollments = await self.db.course_enrollments.find(
                {"student_id": student_id}
            ).to_list(length=None)

            # Calculate totals
            total_class_enrollments = len(class_enrollments)
            total_course_enrollments = len(course_enrollments)
            
            active_class = len([e for e in class_enrollments if e.get("status") == EnrollmentStatus.ACTIVE])
            active_course = len([e for e in course_enrollments if e.get("status") == EnrollmentStatus.ACTIVE])
            active_enrollments = active_class + active_course
            
            completed_class = len([e for e in class_enrollments if e.get("status") == EnrollmentStatus.COMPLETED])
            completed_course = len([e for e in course_enrollments if e.get("status") == EnrollmentStatus.COMPLETED])
            completed_enrollments = completed_class + completed_course

            # Calculate overall progress
            all_enrollments = class_enrollments + course_enrollments
            if all_enrollments:
                overall_progress = sum(e.get("progress_percentage", 0) for e in all_enrollments) / len(all_enrollments)
            else:
                overall_progress = 0.0

            # Calculate total time spent
            total_time_class = sum(e.get("time_spent_minutes", 0) for e in class_enrollments)
            total_time_course = sum(e.get("time_spent_minutes", 0) for e in course_enrollments)
            total_time_spent_minutes = total_time_class + total_time_course

            # Get last activity
            last_activity_at = None
            all_last_activities = [
                e.get("last_activity_at") for e in all_enrollments 
                if e.get("last_activity_at")
            ]
            if all_last_activities:
                last_activity_at = max(all_last_activities)

            # Build response objects (simplified for overview)
            class_enrollment_responses = []
            course_enrollment_responses = []

            return StudentEnrollmentOverview(
                student_id=student_id,
                student_name=student_name,
                total_class_enrollments=total_class_enrollments,
                total_course_enrollments=total_course_enrollments,
                active_enrollments=active_enrollments,
                completed_enrollments=completed_enrollments,
                overall_progress=overall_progress,
                total_time_spent_minutes=total_time_spent_minutes,
                last_activity_at=last_activity_at,
                class_enrollments=class_enrollment_responses,
                course_enrollments=course_enrollment_responses
            )

        except Exception as e:
            logger.error(f"Error getting student enrollment overview: {str(e)}")
            raise

    # Helper Methods
    async def _update_enrollment_progress(
        self, 
        enrollment_id: str, 
        enrollment_type: str,
        activity_type: ActivityType,
        progress_value: float,
        time_spent: int
    ):
        """Update enrollment progress and statistics"""
        try:
            collection = (
                self.db.class_enrollments if enrollment_type == "class" 
                else self.db.course_enrollments
            )
            
            # Update last activity and time spent
            update_data = {
                "last_activity_at": datetime.utcnow(),
                "$inc": {"time_spent_minutes": time_spent}
            }

            # Update specific counters based on activity type
            if activity_type == ActivityType.LESSON_COMPLETE:
                update_data["$inc"]["lessons_completed"] = 1
            elif activity_type == ActivityType.DECK_PRACTICE:
                update_data["$inc"]["decks_practiced"] = 1

            await collection.update_one(
                {"_id": ObjectId(enrollment_id)},
                update_data
            )

            # Recalculate progress percentage
            await self._recalculate_enrollment_progress(enrollment_id, enrollment_type)

        except Exception as e:
            logger.error(f"Error updating enrollment progress: {str(e)}")

    async def _recalculate_enrollment_progress(self, enrollment_id: str, enrollment_type: str):
        """Recalculate and update enrollment progress percentage"""
        try:
            collection = (
                self.db.class_enrollments if enrollment_type == "class" 
                else self.db.course_enrollments
            )
            
            enrollment = await collection.find_one({"_id": ObjectId(enrollment_id)})
            if not enrollment:
                return

            if enrollment_type == "class":
                # For class: progress based on completed courses
                total_courses = enrollment.get("total_courses", 0)
                completed_courses = enrollment.get("completed_courses", 0)
                progress = (completed_courses / total_courses * 100) if total_courses > 0 else 0
            else:
                # For course: progress based on completed lessons
                total_lessons = enrollment.get("total_lessons", 0)
                completed_lessons = enrollment.get("lessons_completed", 0)
                progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

            # Update progress percentage
            await collection.update_one(
                {"_id": ObjectId(enrollment_id)},
                {"$set": {"progress_percentage": min(progress, 100.0)}}
            )

            # Check for completion
            if progress >= 100.0 and enrollment.get("status") == EnrollmentStatus.ACTIVE:
                await collection.update_one(
                    {"_id": ObjectId(enrollment_id)},
                    {
                        "$set": {
                            "status": EnrollmentStatus.COMPLETED,
                            "completion_date": datetime.utcnow()
                        }
                    }
                )

        except Exception as e:
            logger.error(f"Error recalculating progress: {str(e)}")

    async def _get_activity_breakdown(self, enrollment_id: str, enrollment_type: str) -> Dict[str, int]:
        """Get breakdown of activities by type"""
        try:
            pipeline = [
                {"$match": {
                    "enrollment_id": enrollment_id,
                    "enrollment_type": enrollment_type
                }},
                {"$group": {
                    "_id": "$activity_type",
                    "count": {"$sum": 1}
                }}
            ]

            results = await self.db.enrollment_progress.aggregate(pipeline).to_list(length=None)
            
            breakdown = {}
            for result in results:
                breakdown[result["_id"]] = result["count"]

            return breakdown

        except Exception as e:
            logger.error(f"Error getting activity breakdown: {str(e)}")
            return {}

    def _calculate_basic_stats(self, enrollments: List[Dict]) -> Dict[str, Any]:
        """Calculate basic enrollment statistics"""
        total = len(enrollments)
        if total == 0:
            return {
                "total_enrollments": 0,
                "active_enrollments": 0,
                "completed_enrollments": 0,
                "dropped_enrollments": 0,
                "suspended_enrollments": 0,
                "pending_enrollments": 0,
                "waitlisted_enrollments": 0,
                "average_progress": 0.0,
                "completion_rate": 0.0,
                "retention_rate": 0.0,
                "average_time_to_completion_days": 0.0
            }

        # Count by status
        status_counts = defaultdict(int)
        for enrollment in enrollments:
            status_counts[enrollment.get("status", "unknown")] += 1

        # Calculate averages
        avg_progress = sum(e.get("progress_percentage", 0) for e in enrollments) / total
        
        completed = status_counts[EnrollmentStatus.COMPLETED]
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        active_or_completed = status_counts[EnrollmentStatus.ACTIVE] + completed
        retention_rate = (active_or_completed / total) * 100 if total > 0 else 0

        # Calculate average time to completion
        completion_times = []
        for enrollment in enrollments:
            if (enrollment.get("status") == EnrollmentStatus.COMPLETED and 
                enrollment.get("completion_date") and 
                enrollment.get("enrollment_date")):
                
                delta = enrollment["completion_date"] - enrollment["enrollment_date"]
                completion_times.append(delta.days)

        avg_completion_days = sum(completion_times) / len(completion_times) if completion_times else 0

        return {
            "total_enrollments": total,
            "active_enrollments": status_counts[EnrollmentStatus.ACTIVE],
            "completed_enrollments": status_counts[EnrollmentStatus.COMPLETED],
            "dropped_enrollments": status_counts[EnrollmentStatus.DROPPED],
            "suspended_enrollments": status_counts[EnrollmentStatus.SUSPENDED],
            "pending_enrollments": status_counts[EnrollmentStatus.PENDING],
            "waitlisted_enrollments": status_counts[EnrollmentStatus.WAITLISTED],
            "average_progress": avg_progress,
            "completion_rate": completion_rate,
            "retention_rate": retention_rate,
            "average_time_to_completion_days": avg_completion_days
        }


# Create service instance
progress_tracking_service = ProgressTrackingService()
