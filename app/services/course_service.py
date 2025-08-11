"""Course service for managing courses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
import logging

from app.models.course import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
    CourseListResponse,
    CourseFilterRequest,
    CoursesListResponse,
    CourseStatsResponse
)
from app.models.user import User
from app.models.enums import DifficultyLevel

logger = logging.getLogger(__name__)


class CourseService:
    """Service for course operations."""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.courses
    
    async def create_course(self, course_data: CourseCreateRequest, creator: User) -> CourseResponse:
        """Create a new course."""
        try:
            # Prepare course document
            now = datetime.utcnow()
            course_doc = {
                "title": course_data.title,
                "description": course_data.description,
                "category": course_data.category,
                "difficulty_level": course_data.difficulty_level.value,  # Convert enum to string
                "is_public": course_data.is_public,
                "tags": course_data.tags or [],
                "prerequisites": course_data.prerequisites or [],
                "creator_id": str(creator.id),  # Keep as string
                "creator_name": creator.username,
                "estimated_hours": course_data.estimated_hours,
                "created_at": now,
                "updated_at": now,
                "is_active": True,
                "enrollments_count": 0,
                "average_rating": None
            }
            
            # Insert course
            result = await self.collection.insert_one(course_doc)
            
            if not result.inserted_id:
                logger.error("Failed to create course")
                raise Exception("Failed to create course")
            
            # Fetch the created course
            created_course = await self.collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Course created successfully with ID: {result.inserted_id}")
            return self._document_to_response(created_course)
            
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            raise e
    
    async def get_course_by_id(self, course_id: str, requesting_user: User) -> Optional[CourseResponse]:
        """Get a course by ID with visibility check."""
        try:
            course = await self.collection.find_one({"_id": ObjectId(course_id)})
            
            if not course:
                return None
            
            # Check visibility permissions
            if not course.get("is_public", False):
                # Private course - only creator and admin can view
                if course.get("creator_id") != requesting_user.id and requesting_user.role != "admin":
                    return None
            
            return self._document_to_response(course)
            
        except Exception as e:
            logger.error(f"Error fetching course {course_id}: {str(e)}")
            return None
    
    async def update_course(self, course_id: str, course_data: CourseUpdateRequest, requesting_user: User) -> Optional[CourseResponse]:
        """Update a course."""
        try:
            logger.info(f"Attempting to update course {course_id} by user {requesting_user.username}")
            
            # Check if course exists and user has permission
            existing_course = await self.collection.find_one({"_id": ObjectId(course_id)})
            
            if not existing_course:
                logger.warning(f"Course {course_id} not found")
                return None
            
            logger.info(f"Course found. Creator: {existing_course.get('creator_id')}, Requesting user: {requesting_user.id}, User role: {requesting_user.role}")
            
            # Check ownership permissions - ensure both IDs are strings for comparison
            creator_id_str = str(existing_course.get("creator_id"))
            requesting_user_id_str = str(requesting_user.id)
            
            if creator_id_str != requesting_user_id_str and requesting_user.role != "admin":
                logger.warning(f"Permission denied for user {requesting_user.username} to update course {course_id}")
                logger.warning(f"Creator ID: '{creator_id_str}', Requesting user ID: '{requesting_user_id_str}'")
                raise PermissionError("Only course creator or admin can update this course")
            
            # Prepare update data (only include provided fields)
            update_data = {"updated_at": datetime.utcnow()}
            
            logger.info(f"Received course data: {course_data}")
            
            if course_data.title is not None:
                update_data["title"] = course_data.title
            if course_data.description is not None:
                update_data["description"] = course_data.description
            if course_data.category is not None:
                update_data["category"] = course_data.category
            if course_data.difficulty_level is not None:
                # Handle both enum and string values
                if hasattr(course_data.difficulty_level, 'value'):
                    update_data["difficulty_level"] = course_data.difficulty_level.value
                else:
                    update_data["difficulty_level"] = str(course_data.difficulty_level)
                logger.info(f"Setting difficulty_level: {update_data['difficulty_level']}")
            if course_data.is_public is not None:
                update_data["is_public"] = course_data.is_public
            if course_data.tags is not None:
                update_data["tags"] = course_data.tags
            if course_data.prerequisites is not None:
                update_data["prerequisites"] = course_data.prerequisites
            if course_data.estimated_hours is not None:
                update_data["estimated_hours"] = course_data.estimated_hours
            
            logger.info(f"Update data: {update_data}")
            
            # Update course
            result = await self.collection.update_one(
                {"_id": ObjectId(course_id)},
                {"$set": update_data}
            )
            
            logger.info(f"Update result: matched={result.matched_count}, modified={result.modified_count}")
            
            if result.modified_count == 0:
                logger.warning(f"No changes made to course {course_id}")
            
            # Fetch updated course
            updated_course = await self.collection.find_one({"_id": ObjectId(course_id)})
            
            if not updated_course:
                logger.error(f"Could not fetch updated course {course_id}")
                raise Exception("Failed to fetch updated course")
            
            logger.info(f"Course {course_id} updated successfully")
            return self._document_to_response(updated_course)
            
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Error updating course {course_id}: {str(e)}")
            logger.exception("Full traceback:")
            raise e
    
    async def delete_course(self, course_id: str, requesting_user: User) -> bool:
        """Delete a course (soft delete by setting is_active to False)."""
        try:
            # Check if course exists and user has permission
            existing_course = await self.collection.find_one({"_id": ObjectId(course_id)})
            
            if not existing_course:
                return False
            
            # Check ownership permissions - ensure both IDs are strings for comparison
            creator_id_str = str(existing_course.get("creator_id"))
            requesting_user_id_str = str(requesting_user.id)
            
            if creator_id_str != requesting_user_id_str and requesting_user.role != "admin":
                raise PermissionError("Only course creator or admin can delete this course")
            
            # Soft delete by setting is_active to False
            result = await self.collection.update_one(
                {"_id": ObjectId(course_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Course {course_id} deleted successfully")
                return True
            else:
                logger.warning(f"Failed to delete course {course_id}")
                return False
                
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Error deleting course {course_id}: {str(e)}")
            return False
    
    async def get_courses(self, filters: CourseFilterRequest, requesting_user: User, skip: int = 0, limit: int = 20) -> CoursesListResponse:
        """Get courses with filtering and pagination."""
        try:
            # Build query filter
            query = {"is_active": True}
            
            # Public courses or user's own courses (unless admin)
            if requesting_user.role != "admin":
                query["$or"] = [
                    {"is_public": True},
                    {"creator_id": requesting_user.id}  # String comparison
                ]
            
            # Apply filters
            if filters.category:
                query["category"] = filters.category
            
            if filters.difficulty_level:
                query["difficulty_level"] = filters.difficulty_level
            
            if filters.creator_id:
                query["creator_id"] = filters.creator_id  # String comparison
            
            if filters.is_public is not None:
                query["is_public"] = filters.is_public
            
            if filters.tags:
                query["tags"] = {"$in": filters.tags}
            
            if filters.search:
                # Text search in title and description
                query["$or"] = [
                    {"title": {"$regex": filters.search, "$options": "i"}},
                    {"description": {"$regex": filters.search, "$options": "i"}}
                ]
            
            # Get total count
            total_count = await self.collection.count_documents(query)
            
            # Get courses with pagination
            cursor = self.collection.find(query).skip(skip).limit(limit)
            
            # Sort by creation date (newest first) by default
            cursor = cursor.sort("created_at", -1)
            
            courses = await cursor.to_list(length=limit)
            
            # Convert to response objects
            course_responses = [self._document_to_list_response(course) for course in courses]
            
            logger.info(f"Retrieved {len(course_responses)} courses (total: {total_count})")
            
            return CoursesListResponse(
                courses=course_responses,
                total=total_count,
                skip=skip,
                limit=limit,
                has_more=skip + len(course_responses) < total_count
            )
            
        except Exception as e:
            logger.error(f"Error fetching courses: {str(e)}")
            raise e
    
    async def get_course_stats(self, course_id: str, requesting_user: User) -> Optional[CourseStatsResponse]:
        """Get course statistics."""
        try:
            course = await self.collection.find_one({"_id": ObjectId(course_id)})
            
            if not course:
                return None
            
            # Check visibility permissions
            if not course.get("is_public", False):
                if str(course.get("creator_id")) != requesting_user.id and requesting_user.role != "admin":
                    return None
            
            # Get deck count from decks collection
            deck_count = await self.db.decks.count_documents({
                "course_id": ObjectId(course_id),
                "is_active": True
            })
            
            # Get total cards from decks
            pipeline = [
                {"$match": {"course_id": ObjectId(course_id), "is_active": True}},
                {"$group": {"_id": None, "total_cards": {"$sum": "$card_count"}}}
            ]
            
            result = await self.db.decks.aggregate(pipeline).to_list(1)
            total_cards = result[0]["total_cards"] if result else 0
            
            # Get enrollment count (if class enrollments exist)
            enrollments = await self.db.class_enrollments.count_documents({
                "course_id": ObjectId(course_id)
            })
            
            return CourseStatsResponse(
                deck_count=deck_count,
                total_cards=total_cards,
                enrollments=enrollments
            )
            
        except Exception as e:
            logger.error(f"Error fetching course stats for {course_id}: {str(e)}")
            return None
    
    def _document_to_response(self, course_doc: Dict[str, Any]) -> CourseResponse:
        """Convert MongoDB document to CourseResponse."""
        return CourseResponse(
            _id=str(course_doc["_id"]),
            title=course_doc["title"],
            description=course_doc["description"],
            category=course_doc["category"],
            difficulty_level=course_doc["difficulty_level"],
            is_public=course_doc["is_public"],
            tags=course_doc.get("tags", []),
            estimated_hours=course_doc.get("estimated_hours"),
            prerequisites=course_doc.get("prerequisites", []),
            creator_id=course_doc["creator_id"],
            creator_name=course_doc["creator_name"],
            enrollments_count=course_doc.get("enrollments_count", 0),
            average_rating=course_doc.get("average_rating"),
            created_at=course_doc["created_at"],
            updated_at=course_doc["updated_at"]
        )

    def _document_to_list_response(self, course_doc: Dict[str, Any]) -> CourseListResponse:
        """Convert MongoDB document to CourseListResponse."""
        return CourseListResponse(
            _id=str(course_doc["_id"]),
            title=course_doc["title"],
            description=course_doc["description"],
            category=course_doc["category"],
            difficulty_level=course_doc["difficulty_level"],
            is_public=course_doc["is_public"],
            tags=course_doc.get("tags", []),
            estimated_hours=course_doc.get("estimated_hours"),
            creator_name=course_doc["creator_name"],
            enrollments_count=course_doc.get("enrollments_count", 0),
            average_rating=course_doc.get("average_rating"),
            created_at=course_doc["created_at"]
        )
