"""
Lesson service for Phase 5.5 Lesson CRUD Operations
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.database import get_database
from app.models.lesson import (
    LessonCreate, LessonUpdate, LessonResponse, 
    LessonListResponse, LessonStatsResponse,
    LessonPrerequisiteCheck, LessonBulkOrderUpdate
)


class LessonService:
    def __init__(self, db=None):
        self.db = db
        if self.db is not None:
            self.collection = self.db.lessons
        else:
            self.collection = None

    def _document_to_response(self, doc: Dict[str, Any]) -> LessonResponse:
        """Convert MongoDB document to LessonResponse"""
        if not doc:
            return None
        
        # Convert ObjectId to string
        doc['id'] = str(doc['_id'])
        del doc['_id']
        
        return LessonResponse(**doc)

    async def create_lesson(self, course_id: str, lesson_data: LessonCreate, created_by: str) -> LessonResponse:
        """Create a new lesson in a course"""
        
        # For course validation, we'll do a simple check if course exists
        # Since we don't have user object in service layer, we'll do basic validation
        course_doc = await self.db.courses.find_one({
            "_id": ObjectId(course_id),
            "is_active": True
        })
        if not course_doc:
            raise ValueError("Course not found")
        
        # Check for duplicate lesson order in course
        existing_order = await self.collection.find_one({
            "course_id": course_id,
            "lesson_order": lesson_data.lesson_order,
            "is_active": True
        })
        if existing_order:
            raise ValueError(f"Lesson order {lesson_data.lesson_order} already exists in this course")
        
        # Validate prerequisite lessons exist in same course
        if lesson_data.prerequisite_lessons:
            for prereq_id in lesson_data.prerequisite_lessons:
                prereq_lesson = await self.collection.find_one({
                    "_id": ObjectId(prereq_id),
                    "course_id": course_id,
                    "is_active": True
                })
                if not prereq_lesson:
                    raise ValueError(f"Prerequisite lesson {prereq_id} not found in this course")

        # Create lesson document
        lesson_doc = {
            **lesson_data.dict(),
            "course_id": course_id,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }

        # Insert lesson
        result = await self.collection.insert_one(lesson_doc)
        
        # Return created lesson
        created_lesson = await self.collection.find_one({"_id": result.inserted_id})
        return self._document_to_response(created_lesson)

    async def get_lesson(self, lesson_id: str) -> Optional[LessonResponse]:
        """Get a lesson by ID"""
        try:
            lesson = await self.collection.find_one({
                "_id": ObjectId(lesson_id),
                "is_active": True
            })
            return self._document_to_response(lesson)
        except Exception:
            return None

    async def get_course_lessons(
        self, 
        course_id: str, 
        published_only: bool = False,
        page: int = 1, 
        per_page: int = 50
    ) -> LessonListResponse:
        """Get all lessons for a course"""
        
        # Build filter
        filter_query = {
            "course_id": course_id,
            "is_active": True
        }
        
        if published_only:
            filter_query["is_published"] = True

        # Get total count
        total = await self.collection.count_documents(filter_query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page

        # Get lessons with pagination, sorted by lesson_order
        lessons_cursor = self.collection.find(filter_query).sort("lesson_order", 1).skip(skip).limit(per_page)
        lessons = []
        
        async for lesson_doc in lessons_cursor:
            lessons.append(self._document_to_response(lesson_doc))

        return LessonListResponse(
            lessons=lessons,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    async def update_lesson(self, lesson_id: str, lesson_data: LessonUpdate, updated_by: str) -> Optional[LessonResponse]:
        """Update a lesson"""
        try:
            # Get existing lesson
            existing_lesson = await self.collection.find_one({
                "_id": ObjectId(lesson_id),
                "is_active": True
            })
            if not existing_lesson:
                return None

            # Prepare update data
            update_data = {}
            for field, value in lesson_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value

            # Check lesson order conflict if updating order
            if "lesson_order" in update_data:
                existing_order = await self.collection.find_one({
                    "course_id": existing_lesson["course_id"],
                    "lesson_order": update_data["lesson_order"],
                    "is_active": True,
                    "_id": {"$ne": ObjectId(lesson_id)}
                })
                if existing_order:
                    raise ValueError(f"Lesson order {update_data['lesson_order']} already exists in this course")

            # Validate prerequisite lessons if updating
            if "prerequisite_lessons" in update_data and update_data["prerequisite_lessons"]:
                for prereq_id in update_data["prerequisite_lessons"]:
                    prereq_lesson = await self.collection.find_one({
                        "_id": ObjectId(prereq_id),
                        "course_id": existing_lesson["course_id"],
                        "is_active": True
                    })
                    if not prereq_lesson:
                        raise ValueError(f"Prerequisite lesson {prereq_id} not found in this course")

            if not update_data:
                return self._document_to_response(existing_lesson)

            # Add update timestamp
            update_data["updated_at"] = datetime.utcnow()

            # Update lesson
            await self.collection.update_one(
                {"_id": ObjectId(lesson_id)},
                {"$set": update_data}
            )

            # Return updated lesson
            updated_lesson = await self.collection.find_one({"_id": ObjectId(lesson_id)})
            return self._document_to_response(updated_lesson)

        except Exception as e:
            if "already exists" in str(e):
                raise e
            return None

    async def delete_lesson(self, lesson_id: str) -> bool:
        """Soft delete a lesson"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(lesson_id), "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def reorder_lessons(self, course_id: str, order_updates: LessonBulkOrderUpdate) -> bool:
        """Bulk update lesson orders"""
        try:
            # Validate all lessons belong to the course
            lesson_ids = [update.lesson_id for update in order_updates.order_updates]
            lessons = await self.collection.find({
                "_id": {"$in": [ObjectId(lid) for lid in lesson_ids]},
                "course_id": course_id,
                "is_active": True
            }).to_list(length=None)

            if len(lessons) != len(lesson_ids):
                raise ValueError("Some lessons not found in the specified course")

            # Check for duplicate orders
            new_orders = [update.new_order for update in order_updates.order_updates]
            if len(set(new_orders)) != len(new_orders):
                raise ValueError("Duplicate lesson orders provided")

            # Update each lesson order
            for update in order_updates.order_updates:
                await self.collection.update_one(
                    {"_id": ObjectId(update.lesson_id)},
                    {
                        "$set": {
                            "lesson_order": update.new_order,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

            return True
        except Exception:
            return False

    async def get_lesson_stats(self, course_id: str) -> LessonStatsResponse:
        """Get lesson statistics for a course"""
        pipeline = [
            {"$match": {"course_id": course_id, "is_active": True}},
            {
                "$group": {
                    "_id": None,
                    "total_lessons": {"$sum": 1},
                    "published_lessons": {
                        "$sum": {"$cond": [{"$eq": ["$is_published", True]}, 1, 0]}
                    },
                    "draft_lessons": {
                        "$sum": {"$cond": [{"$eq": ["$is_published", False]}, 1, 0]}
                    },
                    "total_duration": {"$sum": {"$ifNull": ["$duration_minutes", 0]}},
                    "lessons_with_duration": {
                        "$sum": {"$cond": [{"$ne": ["$duration_minutes", None]}, 1, 0]}
                    },
                    "lessons_with_prerequisites": {
                        "$sum": {"$cond": [{"$gt": [{"$size": {"$ifNull": ["$prerequisite_lessons", []]}}, 0]}, 1, 0]}
                    },
                    "lessons_with_objectives": {
                        "$sum": {"$cond": [{"$gt": [{"$size": {"$ifNull": ["$learning_objectives", []]}}, 0]}, 1, 0]}
                    },
                    "durations": {"$push": {"$ifNull": ["$duration_minutes", 0]}}
                }
            }
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return LessonStatsResponse(
                total_lessons=0,
                published_lessons=0,
                draft_lessons=0,
                avg_duration_minutes=None,
                total_duration_minutes=0,
                lessons_with_prerequisites=0,
                lessons_with_objectives=0
            )

        stats = result[0]
        
        # Calculate average duration
        durations = [d for d in stats.get("durations", []) if d > 0]
        avg_duration = sum(durations) / len(durations) if durations else None

        return LessonStatsResponse(
            total_lessons=stats.get("total_lessons", 0),
            published_lessons=stats.get("published_lessons", 0),
            draft_lessons=stats.get("draft_lessons", 0),
            avg_duration_minutes=avg_duration,
            total_duration_minutes=stats.get("total_duration", 0),
            lessons_with_prerequisites=stats.get("lessons_with_prerequisites", 0),
            lessons_with_objectives=stats.get("lessons_with_objectives", 0)
        )

    async def check_lesson_prerequisites(self, lesson_id: str, user_id: str) -> LessonPrerequisiteCheck:
        """Check if user has completed prerequisite lessons"""
        
        # Get lesson
        lesson = await self.get_lesson(lesson_id)
        if not lesson:
            return LessonPrerequisiteCheck(
                lesson_id=lesson_id,
                has_access=False,
                missing_prerequisites=[],
                completed_prerequisites=[]
            )

        # If no prerequisites, user has access
        if not lesson.prerequisite_lessons:
            return LessonPrerequisiteCheck(
                lesson_id=lesson_id,
                has_access=True,
                missing_prerequisites=[],
                completed_prerequisites=[]
            )

        # For now, assume all prerequisites are completed
        # This will be enhanced when we implement lesson progress tracking
        return LessonPrerequisiteCheck(
            lesson_id=lesson_id,
            has_access=True,
            missing_prerequisites=[],
            completed_prerequisites=lesson.prerequisite_lessons
        )
