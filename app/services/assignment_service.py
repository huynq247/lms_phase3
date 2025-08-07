"""
Assignment service for managing deck assignments.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.database import get_database
from app.models.assignment import (
    DeckAssignmentCreate, DeckAssignmentResponse, AssignmentListResponse,
    AssignmentType, DeckPrivacyUpdateRequest
)
from app.models.deck import DeckPrivacyLevel
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class AssignmentService:
    """Service for managing deck assignments and privacy."""

    def __init__(self):
        self.db: AsyncIOMotorDatabase = get_database()
        self.assignments_collection = self.db.deck_assignments
        self.decks_collection = self.db.decks
        self.users_collection = self.db.users

    async def create_assignment(
        self,
        assignment_data: DeckAssignmentCreate,
        current_user_id: str
    ) -> Optional[DeckAssignmentResponse]:
        """Create a new deck assignment."""
        try:
            # Verify deck exists and user has permission
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(assignment_data.deck_id)})
            if not deck_doc:
                raise ValueError("Deck not found")

            # Check if user can assign this deck
            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            user_role = current_user.get("role", UserRole.STUDENT)
            
            # Only admins and teachers can make assignments
            # Owners can also assign their own decks
            if (user_role not in [UserRole.ADMIN, UserRole.TEACHER] and 
                str(deck_doc.get("owner_id")) != current_user_id):
                raise ValueError("Permission denied: Cannot assign this deck")

            # Check for existing assignment
            existing = await self.assignments_collection.find_one({
                "deck_id": assignment_data.deck_id,
                "assignment_type": assignment_data.assignment_type,
                "target_id": assignment_data.target_id
            })
            if existing:
                raise ValueError("Assignment already exists")

            # Create assignment document
            assignment_doc = {
                "deck_id": assignment_data.deck_id,
                "assignment_type": assignment_data.assignment_type,
                "target_id": assignment_data.target_id,
                "assigned_by": current_user_id,
                "created_at": datetime.utcnow()
            }

            # Insert assignment
            result = await self.assignments_collection.insert_one(assignment_doc)
            assignment_doc["_id"] = result.inserted_id

            # Update deck's assignment arrays based on type
            update_data = {}
            if assignment_data.assignment_type == AssignmentType.CLASS:
                update_data = {"$addToSet": {"assigned_class_ids": assignment_data.target_id}}
            elif assignment_data.assignment_type == AssignmentType.COURSE:
                update_data = {"$addToSet": {"assigned_course_ids": assignment_data.target_id}}
            elif assignment_data.assignment_type == AssignmentType.LESSON:
                update_data = {"$addToSet": {"assigned_lesson_ids": assignment_data.target_id}}

            if update_data:
                await self.decks_collection.update_one(
                    {"_id": ObjectId(assignment_data.deck_id)},
                    update_data
                )

            # Convert to response
            return await self._convert_to_assignment_response(assignment_doc)

        except Exception as e:
            logger.error(f"Error creating assignment: {str(e)}")
            raise

    async def remove_assignment(
        self,
        assignment_id: str,
        current_user_id: str
    ) -> bool:
        """Remove a deck assignment."""
        try:
            # Get assignment
            assignment_doc = await self.assignments_collection.find_one({"_id": ObjectId(assignment_id)})
            if not assignment_doc:
                return False

            # Check permissions
            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            user_role = current_user.get("role", UserRole.STUDENT)
            
            # Only admins, teachers, or the person who made the assignment can remove it
            if (user_role not in [UserRole.ADMIN, UserRole.TEACHER] and 
                str(assignment_doc.get("assigned_by")) != current_user_id):
                
                # Also check if current user is deck owner
                deck_doc = await self.decks_collection.find_one({"_id": ObjectId(assignment_doc["deck_id"])})
                if not deck_doc or str(deck_doc.get("owner_id")) != current_user_id:
                    raise ValueError("Permission denied: Cannot remove this assignment")

            # Remove from deck's assignment arrays
            update_data = {}
            if assignment_doc["assignment_type"] == AssignmentType.CLASS:
                update_data = {"$pull": {"assigned_class_ids": assignment_doc["target_id"]}}
            elif assignment_doc["assignment_type"] == AssignmentType.COURSE:
                update_data = {"$pull": {"assigned_course_ids": assignment_doc["target_id"]}}
            elif assignment_doc["assignment_type"] == AssignmentType.LESSON:
                update_data = {"$pull": {"assigned_lesson_ids": assignment_doc["target_id"]}}

            if update_data:
                await self.decks_collection.update_one(
                    {"_id": ObjectId(assignment_doc["deck_id"])},
                    update_data
                )

            # Delete assignment
            await self.assignments_collection.delete_one({"_id": ObjectId(assignment_id)})
            return True

        except Exception as e:
            logger.error(f"Error removing assignment: {str(e)}")
            raise

    async def update_deck_privacy(
        self,
        deck_id: str,
        privacy_data: DeckPrivacyUpdateRequest,
        current_user_id: str
    ) -> bool:
        """Update deck privacy level and assignments."""
        try:
            # Get deck
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                raise ValueError("Deck not found")

            # Check permissions
            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            user_role = current_user.get("role", UserRole.STUDENT)
            
            # Only admins, teachers, or deck owner can change privacy
            if (user_role not in [UserRole.ADMIN, UserRole.TEACHER] and 
                str(deck_doc.get("owner_id")) != current_user_id):
                raise ValueError("Permission denied: Cannot modify deck privacy")

            # Validate privacy level
            valid_levels = [
                DeckPrivacyLevel.PRIVATE,
                DeckPrivacyLevel.CLASS_ASSIGNED,
                DeckPrivacyLevel.COURSE_ASSIGNED,
                DeckPrivacyLevel.LESSON_ASSIGNED,
                DeckPrivacyLevel.PUBLIC
            ]
            if privacy_data.privacy_level not in valid_levels:
                raise ValueError(f"Invalid privacy level. Must be one of: {valid_levels}")

            # Prepare update data
            update_data = {
                "privacy_level": privacy_data.privacy_level,
                "assigned_class_ids": privacy_data.assigned_class_ids,
                "assigned_course_ids": privacy_data.assigned_course_ids,
                "assigned_lesson_ids": privacy_data.assigned_lesson_ids,
                "updated_at": datetime.utcnow()
            }

            # Update deck
            await self.decks_collection.update_one(
                {"_id": ObjectId(deck_id)},
                {"$set": update_data}
            )

            return True

        except Exception as e:
            logger.error(f"Error updating deck privacy: {str(e)}")
            raise

    async def get_deck_assignments(
        self,
        deck_id: str,
        current_user_id: str,
        page: int = 1,
        limit: int = 10
    ) -> AssignmentListResponse:
        """Get assignments for a specific deck."""
        try:
            # Verify user can view this deck
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                raise ValueError("Deck not found")

            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            user_role = current_user.get("role", UserRole.STUDENT)
            
            # Check if user can view assignments
            if (user_role not in [UserRole.ADMIN, UserRole.TEACHER] and 
                str(deck_doc.get("owner_id")) != current_user_id):
                raise ValueError("Permission denied: Cannot view deck assignments")

            # Get assignments with pagination
            skip = (page - 1) * limit
            cursor = self.assignments_collection.find({"deck_id": deck_id}).skip(skip).limit(limit)
            
            assignments = []
            async for assignment_doc in cursor:
                assignment_response = await self._convert_to_assignment_response(assignment_doc)
                assignments.append(assignment_response)

            # Count total
            total_count = await self.assignments_collection.count_documents({"deck_id": deck_id})
            
            # Calculate pagination
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1

            return AssignmentListResponse(
                assignments=assignments,
                total_count=total_count,
                page=page,
                limit=limit,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev
            )

        except Exception as e:
            logger.error(f"Error getting deck assignments: {str(e)}")
            raise

    async def _convert_to_assignment_response(self, assignment_doc: Dict[str, Any]) -> DeckAssignmentResponse:
        """Convert assignment document to response model."""
        # Get deck title
        deck_doc = await self.decks_collection.find_one({"_id": ObjectId(assignment_doc["deck_id"])})
        deck_title = deck_doc.get("title") if deck_doc else None

        # Get assigned by username
        user_doc = await self.users_collection.find_one({"_id": ObjectId(assignment_doc["assigned_by"])})
        assigned_by_username = user_doc.get("username") if user_doc else None

        return DeckAssignmentResponse(
            _id=str(assignment_doc["_id"]),
            deck_id=assignment_doc["deck_id"],
            assignment_type=assignment_doc["assignment_type"],
            target_id=assignment_doc["target_id"],
            assigned_by=assignment_doc["assigned_by"],
            created_at=assignment_doc["created_at"],
            deck_title=deck_title,
            assigned_by_username=assigned_by_username
        )
