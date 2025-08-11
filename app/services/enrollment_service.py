"""
Multi-Level Enrollment Service for Phase 5.7
Comprehensive enrollment management across classes and courses
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from pymongo import UpdateOne, InsertOne
from pymongo.errors import BulkWriteError, DuplicateKeyError
import logging

from app.core.deps import get_database
from app.models.enrollment import (
    ClassEnrollmentCreate, ClassEnrollmentUpdate, ClassEnrollmentResponse,
    CourseEnrollmentCreate, CourseEnrollmentUpdate, CourseEnrollmentResponse,
    EnrollmentProgressCreate, EnrollmentProgressResponse,
    EnrollmentStats, ClassEnrollmentStats, CourseEnrollmentStats,
    StudentEnrollmentOverview, BulkEnrollmentCreate, BulkEnrollmentResult,
    EnrollmentStatusUpdate, EnrollmentFilter, EnrollmentSearchQuery,
    EnrollmentListResponse, ProgressListResponse,
    EnrollmentStatus, EnrollmentType, ActivityType
)

logger = logging.getLogger(__name__)


class EnrollmentService:
    """Service for managing multi-level enrollments"""

    def __init__(self):
        self.db = None

    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()

    # Class Enrollment Methods
    async def create_class_enrollment(
        self, 
        enrollment_data: ClassEnrollmentCreate, 
        enrolled_by: str
    ) -> ClassEnrollmentResponse:
        """Create a new class enrollment"""
        await self.initialize()
        
        try:
            # Check if student is already enrolled in this class
            existing = await self.db.class_enrollments.find_one({
                "class_id": enrollment_data.class_id,
                "student_id": enrollment_data.student_id,
                "status": {"$in": [EnrollmentStatus.ACTIVE, EnrollmentStatus.PENDING]}
            })
            
            if existing:
                raise ValueError(f"Student already enrolled in class {enrollment_data.class_id}")

            # Get class information
            class_info = await self.db.classes.find_one({"_id": ObjectId(enrollment_data.class_id)})
            if not class_info:
                raise ValueError(f"Class {enrollment_data.class_id} not found")

            # Prepare enrollment document
            now = datetime.utcnow()
            enrollment_doc = {
                "_id": ObjectId(),
                "class_id": enrollment_data.class_id,
                "student_id": enrollment_data.student_id,
                "enrollment_type": enrollment_data.enrollment_type,
                "status": EnrollmentStatus.ACTIVE,
                "enrollment_date": now,
                "enrolled_by": enrolled_by,
                "progress_percentage": 0.0,
                "last_activity_at": None,
                "completion_date": None,
                "courses_enrolled": [],
                "total_courses": len(class_info.get("course_ids", [])),
                "completed_courses": 0,
                "notes": enrollment_data.notes,
                "metadata": {},
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }

            # Insert enrollment
            await self.db.class_enrollments.insert_one(enrollment_doc)

            # Auto-enroll in courses if requested
            if enrollment_data.auto_enroll_courses and class_info.get("course_ids"):
                course_enrollments = []
                for course_id in class_info["course_ids"]:
                    course_enrollment = {
                        "_id": ObjectId(),
                        "course_id": course_id,
                        "student_id": enrollment_data.student_id,
                        "enrollment_type": EnrollmentType.CLASS_BASED,
                        "class_enrollment_id": str(enrollment_doc["_id"]),
                        "status": EnrollmentStatus.ACTIVE,
                        "enrollment_date": now,
                        "enrolled_by": enrolled_by,
                        "progress_percentage": 0.0,
                        "last_activity_at": None,
                        "completion_date": None,
                        "lessons_completed": 0,
                        "total_lessons": 0,
                        "decks_practiced": 0,
                        "total_decks": 0,
                        "time_spent_minutes": 0,
                        "notes": f"Auto-enrolled from class: {class_info.get('title', 'Unknown')}",
                        "metadata": {"auto_enrolled": True, "class_id": enrollment_data.class_id},
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now
                    }
                    course_enrollments.append(course_enrollment)

                if course_enrollments:
                    await self.db.course_enrollments.insert_many(course_enrollments)
                    enrollment_doc["courses_enrolled"] = [str(ce["_id"]) for ce in course_enrollments]
                    await self.db.class_enrollments.update_one(
                        {"_id": enrollment_doc["_id"]},
                        {"$set": {"courses_enrolled": enrollment_doc["courses_enrolled"]}}
                    )

            # Prepare response
            response_data = {
                **enrollment_doc,
                "id": str(enrollment_doc["_id"]),
                "class_title": class_info.get("title"),
                "class_description": class_info.get("description")
            }
            response_data.pop("_id")

            logger.info(f"Created class enrollment {response_data['id']} for student {enrollment_data.student_id}")
            return ClassEnrollmentResponse(**response_data)

        except Exception as e:
            logger.error(f"Error creating class enrollment: {str(e)}")
            raise

    async def create_course_enrollment(
        self, 
        enrollment_data: CourseEnrollmentCreate, 
        enrolled_by: str
    ) -> CourseEnrollmentResponse:
        """Create a new course enrollment"""
        await self.initialize()
        
        try:
            # Check if student is already enrolled in this course
            existing = await self.db.course_enrollments.find_one({
                "course_id": enrollment_data.course_id,
                "student_id": enrollment_data.student_id,
                "status": {"$in": [EnrollmentStatus.ACTIVE, EnrollmentStatus.PENDING]}
            })
            
            if existing:
                raise ValueError(f"Student already enrolled in course {enrollment_data.course_id}")

            # Get course information
            course_info = await self.db.courses.find_one({"_id": ObjectId(enrollment_data.course_id)})
            if not course_info:
                raise ValueError(f"Course {enrollment_data.course_id} not found")

            # Check prerequisites if requested
            if enrollment_data.prerequisites_check:
                prerequisites_met = await self._check_course_prerequisites(
                    enrollment_data.course_id, 
                    enrollment_data.student_id
                )
                if not prerequisites_met:
                    raise ValueError("Course prerequisites not met")

            # Get lesson and deck counts
            lesson_count = await self.db.lessons.count_documents({"course_id": enrollment_data.course_id})
            deck_count = await self.db.lesson_deck_assignments.count_documents({
                "lesson_id": {"$in": await self._get_course_lesson_ids(enrollment_data.course_id)}
            })

            # Prepare enrollment document
            now = datetime.utcnow()
            enrollment_doc = {
                "_id": ObjectId(),
                "course_id": enrollment_data.course_id,
                "student_id": enrollment_data.student_id,
                "enrollment_type": enrollment_data.enrollment_type,
                "class_enrollment_id": enrollment_data.class_enrollment_id,
                "status": EnrollmentStatus.ACTIVE,
                "enrollment_date": now,
                "enrolled_by": enrolled_by,
                "progress_percentage": 0.0,
                "last_activity_at": None,
                "completion_date": None,
                "lessons_completed": 0,
                "total_lessons": lesson_count,
                "decks_practiced": 0,
                "total_decks": deck_count,
                "time_spent_minutes": 0,
                "notes": enrollment_data.notes,
                "metadata": {},
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }

            # Insert enrollment
            await self.db.course_enrollments.insert_one(enrollment_doc)

            # Get class information if class-based
            class_title = None
            if enrollment_data.class_enrollment_id:
                class_enrollment = await self.db.class_enrollments.find_one({
                    "_id": ObjectId(enrollment_data.class_enrollment_id)
                })
                if class_enrollment:
                    class_info = await self.db.classes.find_one({
                        "_id": ObjectId(class_enrollment["class_id"])
                    })
                    class_title = class_info.get("title") if class_info else None

            # Prepare response
            response_data = {
                **enrollment_doc,
                "id": str(enrollment_doc["_id"]),
                "course_title": course_info.get("title"),
                "course_description": course_info.get("description"),
                "class_title": class_title
            }
            response_data.pop("_id")

            logger.info(f"Created course enrollment {response_data['id']} for student {enrollment_data.student_id}")
            return CourseEnrollmentResponse(**response_data)

        except Exception as e:
            logger.error(f"Error creating course enrollment: {str(e)}")
            raise

    async def get_class_enrollment(self, enrollment_id: str) -> Optional[ClassEnrollmentResponse]:
        """Get a class enrollment by ID"""
        await self.initialize()
        
        try:
            enrollment = await self.db.class_enrollments.find_one({"_id": ObjectId(enrollment_id)})
            if not enrollment:
                return None

            # Get class information
            class_info = await self.db.classes.find_one({"_id": ObjectId(enrollment["class_id"])})

            response_data = {
                **enrollment,
                "id": str(enrollment["_id"]),
                "class_title": class_info.get("title") if class_info else None,
                "class_description": class_info.get("description") if class_info else None
            }
            response_data.pop("_id")

            return ClassEnrollmentResponse(**response_data)

        except Exception as e:
            logger.error(f"Error getting class enrollment {enrollment_id}: {str(e)}")
            raise

    async def get_course_enrollment(self, enrollment_id: str) -> Optional[CourseEnrollmentResponse]:
        """Get a course enrollment by ID"""
        await self.initialize()
        
        try:
            enrollment = await self.db.course_enrollments.find_one({"_id": ObjectId(enrollment_id)})
            if not enrollment:
                return None

            # Get course information
            course_info = await self.db.courses.find_one({"_id": ObjectId(enrollment["course_id"])})

            # Get class information if applicable
            class_title = None
            if enrollment.get("class_enrollment_id"):
                class_enrollment = await self.db.class_enrollments.find_one({
                    "_id": ObjectId(enrollment["class_enrollment_id"])
                })
                if class_enrollment:
                    class_info = await self.db.classes.find_one({
                        "_id": ObjectId(class_enrollment["class_id"])
                    })
                    class_title = class_info.get("title") if class_info else None

            response_data = {
                **enrollment,
                "id": str(enrollment["_id"]),
                "course_title": course_info.get("title") if course_info else None,
                "course_description": course_info.get("description") if course_info else None,
                "class_title": class_title
            }
            response_data.pop("_id")

            return CourseEnrollmentResponse(**response_data)

        except Exception as e:
            logger.error(f"Error getting course enrollment {enrollment_id}: {str(e)}")
            raise

    async def update_class_enrollment(
        self, 
        enrollment_id: str, 
        update_data: ClassEnrollmentUpdate
    ) -> Optional[ClassEnrollmentResponse]:
        """Update a class enrollment"""
        await self.initialize()
        
        try:
            update_dict = update_data.dict(exclude_unset=True)
            if not update_dict:
                # If no updates, return current enrollment
                return await self.get_class_enrollment(enrollment_id)

            update_dict["updated_at"] = datetime.utcnow()

            result = await self.db.class_enrollments.update_one(
                {"_id": ObjectId(enrollment_id)},
                {"$set": update_dict}
            )

            if result.matched_count == 0:
                return None

            logger.info(f"Updated class enrollment {enrollment_id}")
            return await self.get_class_enrollment(enrollment_id)

        except Exception as e:
            logger.error(f"Error updating class enrollment {enrollment_id}: {str(e)}")
            raise

    async def update_course_enrollment(
        self, 
        enrollment_id: str, 
        update_data: CourseEnrollmentUpdate
    ) -> Optional[CourseEnrollmentResponse]:
        """Update a course enrollment"""
        await self.initialize()
        
        try:
            update_dict = update_data.dict(exclude_unset=True)
            if not update_dict:
                # If no updates, return current enrollment
                return await self.get_course_enrollment(enrollment_id)

            update_dict["updated_at"] = datetime.utcnow()

            result = await self.db.course_enrollments.update_one(
                {"_id": ObjectId(enrollment_id)},
                {"$set": update_dict}
            )

            if result.matched_count == 0:
                return None

            logger.info(f"Updated course enrollment {enrollment_id}")
            return await self.get_course_enrollment(enrollment_id)

        except Exception as e:
            logger.error(f"Error updating course enrollment {enrollment_id}: {str(e)}")
            raise

    async def delete_class_enrollment(self, enrollment_id: str) -> bool:
        """Delete a class enrollment and related course enrollments"""
        await self.initialize()
        
        try:
            # Get enrollment first
            enrollment = await self.db.class_enrollments.find_one({"_id": ObjectId(enrollment_id)})
            if not enrollment:
                return False

            # Delete related course enrollments
            await self.db.course_enrollments.delete_many({
                "class_enrollment_id": enrollment_id
            })

            # Delete class enrollment
            result = await self.db.class_enrollments.delete_one({"_id": ObjectId(enrollment_id)})

            logger.info(f"Deleted class enrollment {enrollment_id}")
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting class enrollment {enrollment_id}: {str(e)}")
            raise

    async def delete_course_enrollment(self, enrollment_id: str) -> bool:
        """Delete a course enrollment"""
        await self.initialize()
        
        try:
            result = await self.db.course_enrollments.delete_one({"_id": ObjectId(enrollment_id)})

            if result.deleted_count > 0:
                logger.info(f"Deleted course enrollment {enrollment_id}")

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting course enrollment {enrollment_id}: {str(e)}")
            raise

    # Helper Methods
    async def _check_course_prerequisites(self, course_id: str, student_id: str) -> bool:
        """Check if student meets course prerequisites"""
        try:
            course = await self.db.courses.find_one({"_id": ObjectId(course_id)})
            if not course or not course.get("prerequisites"):
                return True  # No prerequisites required

            for prereq_id in course["prerequisites"]:
                completed = await self.db.course_enrollments.find_one({
                    "course_id": prereq_id,
                    "student_id": student_id,
                    "status": EnrollmentStatus.COMPLETED
                })
                if not completed:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking prerequisites for course {course_id}: {str(e)}")
            return False

    async def _get_course_lesson_ids(self, course_id: str) -> List[str]:
        """Get all lesson IDs for a course"""
        try:
            lessons = await self.db.lessons.find(
                {"course_id": course_id},
                {"_id": 1}
            ).to_list(length=None)
            
            return [str(lesson["_id"]) for lesson in lessons]

        except Exception as e:
            logger.error(f"Error getting lesson IDs for course {course_id}: {str(e)}")
            return []

    # Student Overview Method (Phase 5.7)
    async def get_student_enrollment_overview(self, student_id: str) -> StudentEnrollmentOverview:
        """Get comprehensive enrollment overview for a student"""
        await self.initialize()
        
        try:
            # Get class enrollments
            class_enrollments = await self.db.class_enrollments.find({
                "student_id": student_id
            }).to_list(length=None)
            
            # Get course enrollments  
            course_enrollments = await self.db.course_enrollments.find({
                "student_id": student_id
            }).to_list(length=None)
            
            # Calculate stats
            total_classes = len(class_enrollments)
            total_courses = len(course_enrollments)
            
            active_classes = len([e for e in class_enrollments if e.get("status") == "active"])
            active_courses = len([e for e in course_enrollments if e.get("status") == "active"])
            
            completed_classes = len([e for e in class_enrollments if e.get("status") == "completed"])
            completed_courses = len([e for e in course_enrollments if e.get("status") == "completed"])
            
            # Calculate overall progress
            all_progress = []
            for enrollment in class_enrollments + course_enrollments:
                if enrollment.get("progress_percentage"):
                    all_progress.append(enrollment["progress_percentage"])
            
            overall_progress = sum(all_progress) / len(all_progress) if all_progress else 0.0
            
            # Recent activity
            recent_activity = await self.db.enrollment_progress.find({
                "student_id": student_id
            }).sort("activity_date", -1).limit(5).to_list(length=5)
            
            return StudentEnrollmentOverview(
                student_id=student_id,
                student_name=None,  # Can be populated from user data if needed
                total_class_enrollments=total_classes,
                total_course_enrollments=total_courses,
                active_enrollments=active_classes + active_courses,
                completed_enrollments=completed_classes + completed_courses,
                overall_progress=overall_progress,
                total_time_spent_minutes=0,  # Can be calculated from activity data
                last_activity_at=recent_activity[0].get("activity_date") if recent_activity else None,
                class_enrollments=[ClassEnrollmentResponse(**self._format_class_enrollment(e)) for e in class_enrollments],
                course_enrollments=[CourseEnrollmentResponse(**self._format_course_enrollment(e)) for e in course_enrollments]
            )
            
        except Exception as e:
            logger.error(f"Error getting student enrollment overview: {str(e)}")
            raise

    def _format_class_enrollment(self, enrollment: Dict) -> Dict:
        """Format class enrollment for response"""
        return {
            "id": str(enrollment["_id"]),
            "class_id": enrollment["class_id"],
            "student_id": enrollment["student_id"],
            "enrollment_date": enrollment["enrollment_date"],
            "status": enrollment.get("status", "active"),
            "progress_percentage": enrollment.get("progress_percentage", 0.0),
            "last_activity_at": enrollment.get("last_activity_at"),
            "completion_date": enrollment.get("completion_date"),
            "enrolled_by": enrollment.get("enrolled_by"),
            "auto_enrolled_courses": enrollment.get("auto_enrolled_courses", []),
            "metadata": enrollment.get("metadata", {})
        }

    def _format_course_enrollment(self, enrollment: Dict) -> Dict:
        """Format course enrollment for response"""
        return {
            "id": str(enrollment["_id"]),
            "course_id": enrollment["course_id"],
            "student_id": enrollment["student_id"],
            "enrollment_type": enrollment.get("enrollment_type", "individual"),
            "class_enrollment_id": enrollment.get("class_enrollment_id"),
            "enrollment_date": enrollment["enrollment_date"],
            "status": enrollment.get("status", "active"),
            "progress_percentage": enrollment.get("progress_percentage", 0.0),
            "lessons_completed": enrollment.get("lessons_completed", 0),
            "total_lessons": enrollment.get("total_lessons", 0),
            "last_activity_at": enrollment.get("last_activity_at"),
            "completion_date": enrollment.get("completion_date"),
            "metadata": enrollment.get("metadata", {})
        }

    async def get_enrollment_analytics(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        class_ids: Optional[List[str]] = None,
        course_ids: Optional[List[str]] = None,
        requester_id: str = None
    ) -> Dict[str, Any]:
        """Get enrollment analytics and metrics"""
        await self.initialize()
        
        try:
            # Simple analytics for now
            total_class_enrollments = await self.db.class_enrollments.count_documents({})
            total_course_enrollments = await self.db.course_enrollments.count_documents({})
            
            active_class_enrollments = await self.db.class_enrollments.count_documents({"status": "active"})
            active_course_enrollments = await self.db.course_enrollments.count_documents({"status": "active"})
            
            return {
                "summary": {
                    "total_class_enrollments": total_class_enrollments,
                    "total_course_enrollments": total_course_enrollments,
                    "active_class_enrollments": active_class_enrollments,
                    "active_course_enrollments": active_course_enrollments,
                    "total_active_enrollments": active_class_enrollments + active_course_enrollments
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
                "generated_by": requester_id
            }
            
        except Exception as e:
            logger.error(f"Error getting enrollment analytics: {str(e)}")
            raise


# Create service instance
enrollment_service = EnrollmentService()
