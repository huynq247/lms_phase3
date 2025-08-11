"""
Flashcard service for multimedia content management.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.database import db
from app.models.flashcard import (
    FlashcardCreateRequest, FlashcardUpdateRequest, FlashcardResponse,
    FlashcardListResponse, FlashcardBulkCreateRequest, FlashcardBulkCreateResponse
)
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class FlashcardService:
    """Service for flashcard management with multimedia support."""

    def __init__(self):
        # Defer actual collection binding until first use (DB may not be connected at import time)
        self.db = db.database
        self.flashcards_collection = getattr(self.db, "flashcards", None) if self.db is not None else None
        self.decks_collection = getattr(self.db, "decks", None) if self.db is not None else None
        self.users_collection = getattr(self.db, "users", None) if self.db is not None else None

    def _ensure_collections(self):
        """Lazy initialize collections after DB connection is established."""
        if self.flashcards_collection is None or self.decks_collection is None or self.users_collection is None:
            self.db = db.database
            if self.db is None:
                raise RuntimeError("Database not initialized")
            self.flashcards_collection = self.db.flashcards
            self.decks_collection = self.db.decks
            self.users_collection = self.db.users

    async def get_deck_flashcards(
        self,
        deck_id: str,
        current_user_id: str,
        page: int = 1,
        limit: int = 10,
        difficulty_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        search_query: Optional[str] = None
    ) -> FlashcardListResponse:
        """Get paginated flashcards for a deck with filtering."""
        self._ensure_collections()
        try:
            # Verify deck exists and user has access
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                raise ValueError("Deck not found")

            # Check deck access permission
            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            if not await self._can_view_deck(deck_doc, current_user):
                raise PermissionError("Access denied to this deck")

            # Build query
            query = {"deck_id": deck_id}
            
            # Apply filters
            if difficulty_filter:
                query["difficulty_level"] = difficulty_filter
            
            if tags_filter:
                query["tags"] = {"$in": tags_filter}
            
            if search_query:
                search_regex = {"$regex": search_query, "$options": "i"}
                query["$or"] = [
                    {"front.text": search_regex},
                    {"back.text": search_regex},
                    {"hint": search_regex},
                    {"explanation": search_regex}
                ]

            # Count total
            total_count = await self.flashcards_collection.count_documents(query)

            # Get flashcards with pagination
            skip = (page - 1) * limit
            cursor = self.flashcards_collection.find(query).skip(skip).limit(limit).sort("order_index", 1)

            flashcards = []
            async for flashcard_doc in cursor:
                flashcard_response = await self._convert_to_flashcard_response(flashcard_doc)
                flashcards.append(flashcard_response)

            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1

            # Deck info for response
            deck_info = {
                "id": str(deck_doc["_id"]),
                "title": deck_doc["title"],
                "description": deck_doc.get("description", "")
            }

            return FlashcardListResponse(
                flashcards=flashcards,
                total_count=total_count,
                page=page,
                limit=limit,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
                deck_info=deck_info
            )

        except Exception as e:
            logger.error(f"Error getting flashcards for deck {deck_id}: {str(e)}")
            raise

    async def create_flashcard(
        self,
        deck_id: str,
        flashcard_data: FlashcardCreateRequest,
        current_user_id: str
    ) -> FlashcardResponse:
        """Create a new flashcard in a deck."""
        self._ensure_collections()
        try:
            # Verify deck exists and user has edit permission
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                raise ValueError("Deck not found")

            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            if not await self._can_edit_deck(deck_doc, current_user):
                raise PermissionError("Permission denied to edit this deck")

            # Get next order index
            last_flashcard = await self.flashcards_collection.find_one(
                {"deck_id": deck_id},
                sort=[("order_index", -1)]
            )
            next_order = (last_flashcard["order_index"] + 1) if last_flashcard else 1

            # Prepare flashcard document
            flashcard_doc = {
                "deck_id": deck_id,
                "front": flashcard_data.front.dict(),
                "back": flashcard_data.back.dict(),
                "hint": flashcard_data.hint,
                "explanation": flashcard_data.explanation,
                "difficulty_level": flashcard_data.difficulty_level,
                "tags": flashcard_data.tags,
                "order_index": next_order,
                "created_by": current_user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "times_reviewed": 0,
                "last_reviewed": None
            }

            # Insert flashcard
            result = await self.flashcards_collection.insert_one(flashcard_doc)
            flashcard_doc["_id"] = result.inserted_id

            # Update deck's total_cards count
            await self.decks_collection.update_one(
                {"_id": ObjectId(deck_id)},
                {"$inc": {"total_cards": 1}, "$set": {"updated_at": datetime.utcnow()}}
            )

            # Convert to response
            flashcard_response = await self._convert_to_flashcard_response(flashcard_doc)

            logger.info(f"Created flashcard {result.inserted_id} in deck {deck_id} by user {current_user_id}")
            return flashcard_response

        except Exception as e:
            logger.error(f"Error creating flashcard in deck {deck_id}: {str(e)}")
            raise

    async def get_flashcard_by_id(
        self,
        flashcard_id: str,
        current_user_id: str
    ) -> Optional[FlashcardResponse]:
        """Get a specific flashcard by ID."""
        self._ensure_collections()
        try:
            # Get flashcard
            flashcard_doc = await self.flashcards_collection.find_one({"_id": ObjectId(flashcard_id)})
            if not flashcard_doc:
                return None

            # Check deck access
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(flashcard_doc["deck_id"])})
            if not deck_doc:
                return None

            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                return None

            if not await self._can_view_deck(deck_doc, current_user):
                return None

            # Convert to response
            flashcard_response = await self._convert_to_flashcard_response(flashcard_doc)
            return flashcard_response

        except Exception as e:
            logger.error(f"Error getting flashcard {flashcard_id}: {str(e)}")
            raise

    async def update_flashcard(
        self,
        flashcard_id: str,
        flashcard_data: FlashcardUpdateRequest,
        current_user_id: str
    ) -> Optional[FlashcardResponse]:
        """Update an existing flashcard."""
        self._ensure_collections()
        try:
            # Get flashcard and verify it exists
            flashcard_doc = await self.flashcards_collection.find_one({"_id": ObjectId(flashcard_id)})
            if not flashcard_doc:
                raise ValueError("Flashcard not found")

            # Check deck edit permission
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(flashcard_doc["deck_id"])})
            if not deck_doc:
                raise ValueError("Deck not found")

            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            if not await self._can_edit_deck(deck_doc, current_user):
                raise PermissionError("Permission denied to edit this flashcard")

            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}

            # Update fields that are provided
            flashcard_dict = flashcard_data.model_dump(exclude_unset=True)
            for field, value in flashcard_dict.items():
                if value is not None:
                    update_data[field] = value

            # Update flashcard
            await self.flashcards_collection.update_one(
                {"_id": ObjectId(flashcard_id)},
                {"$set": update_data}
            )

            # Update deck's updated_at timestamp
            await self.decks_collection.update_one(
                {"_id": ObjectId(flashcard_doc["deck_id"])},
                {"$set": {"updated_at": datetime.utcnow()}}
            )

            # Get updated flashcard
            updated_flashcard = await self.flashcards_collection.find_one({"_id": ObjectId(flashcard_id)})
            flashcard_response = await self._convert_to_flashcard_response(updated_flashcard)

            logger.info(f"Updated flashcard {flashcard_id} by user {current_user_id}")
            return flashcard_response

        except Exception as e:
            logger.error(f"Error updating flashcard {flashcard_id}: {str(e)}")
            raise

    async def delete_flashcard(
        self,
        flashcard_id: str,
        current_user_id: str
    ) -> bool:
        """Delete a flashcard."""
        self._ensure_collections()
        try:
            # Get flashcard and verify it exists
            flashcard_doc = await self.flashcards_collection.find_one({"_id": ObjectId(flashcard_id)})
            if not flashcard_doc:
                return False

            # Check deck edit permission
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(flashcard_doc["deck_id"])})
            if not deck_doc:
                return False

            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                return False

            if not await self._can_edit_deck(deck_doc, current_user):
                raise PermissionError("Permission denied to delete this flashcard")

            # Delete flashcard
            result = await self.flashcards_collection.delete_one({"_id": ObjectId(flashcard_id)})

            if result.deleted_count > 0:
                # Update deck's total_cards count
                await self.decks_collection.update_one(
                    {"_id": ObjectId(flashcard_doc["deck_id"])},
                    {"$inc": {"total_cards": -1}, "$set": {"updated_at": datetime.utcnow()}}
                )

                logger.info(f"Deleted flashcard {flashcard_id} by user {current_user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting flashcard {flashcard_id}: {str(e)}")
            raise

    async def bulk_create_flashcards(
        self,
        deck_id: str,
        bulk_data: FlashcardBulkCreateRequest,
        current_user_id: str
    ) -> FlashcardBulkCreateResponse:
        """Create multiple flashcards at once."""
        self._ensure_collections()
        try:
            # Verify deck exists and user has edit permission
            deck_doc = await self.decks_collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                raise ValueError("Deck not found")

            current_user = await self.users_collection.find_one({"_id": ObjectId(current_user_id)})
            if not current_user:
                raise ValueError("User not found")

            if not await self._can_edit_deck(deck_doc, current_user):
                raise PermissionError("Permission denied to edit this deck")

            # Get starting order index
            last_flashcard = await self.flashcards_collection.find_one(
                {"deck_id": deck_id},
                sort=[("order_index", -1)]
            )
            next_order = (last_flashcard["order_index"] + 1) if last_flashcard else 1

            created_flashcards = []
            errors = []

            for i, flashcard_data in enumerate(bulk_data.flashcards):
                try:
                    # Prepare flashcard document
                    flashcard_doc = {
                        "deck_id": deck_id,
                        "front": flashcard_data.front.dict(),
                        "back": flashcard_data.back.dict(),
                        "hint": flashcard_data.hint,
                        "explanation": flashcard_data.explanation,
                        "difficulty_level": flashcard_data.difficulty_level,
                        "tags": flashcard_data.tags,
                        "order_index": next_order + i,
                        "created_by": current_user_id,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "times_reviewed": 0,
                        "last_reviewed": None
                    }

                    # Insert flashcard
                    result = await self.flashcards_collection.insert_one(flashcard_doc)
                    flashcard_doc["_id"] = result.inserted_id

                    # Convert to response
                    flashcard_response = await self._convert_to_flashcard_response(flashcard_doc)
                    created_flashcards.append(flashcard_response)

                except Exception as e:
                    errors.append(f"Flashcard {i + 1}: {str(e)}")

            # Update deck's total_cards count
            if created_flashcards:
                await self.decks_collection.update_one(
                    {"_id": ObjectId(deck_id)},
                    {
                        "$inc": {"total_cards": len(created_flashcards)},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )

            logger.info(f"Bulk created {len(created_flashcards)} flashcards in deck {deck_id} by user {current_user_id}")

            return FlashcardBulkCreateResponse(
                created_count=len(created_flashcards),
                flashcards=created_flashcards,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Error bulk creating flashcards in deck {deck_id}: {str(e)}")
            raise

    async def _can_view_deck(self, deck_doc: Dict, current_user: Dict) -> bool:
        """Check if user can view the deck."""
        user_role = current_user.get("role", UserRole.STUDENT)
        user_id = str(current_user["_id"])

        # Admin can view any deck
        if user_role == UserRole.ADMIN:
            return True

        # Owner can always view their deck
        if deck_doc.get("owner_id") == user_id:
            return True

        # Public decks are viewable by everyone
        if deck_doc.get("privacy_level") == "public":
            return True

        # For assigned decks, check if user is in the assignment list
        privacy_level = deck_doc.get("privacy_level")
        if privacy_level == "class-assigned":
            # TODO: Check if user is in assigned classes
            return True
        elif privacy_level == "course-assigned":
            # TODO: Check if user is in assigned courses
            return True
        elif privacy_level == "lesson-assigned":
            # TODO: Check if user is in assigned lessons
            return True

        # Private decks - only owner and admin
        return False

    async def _can_edit_deck(self, deck_doc: Dict, current_user: Dict) -> bool:
        """Check if user can edit the deck."""
        user_role = current_user.get("role", UserRole.STUDENT)
        user_id = str(current_user["_id"])

        # Admin can edit any deck
        if user_role == UserRole.ADMIN:
            return True

        # Owner can edit their deck
        if deck_doc.get("owner_id") == user_id:
            return True

        return False

    async def _convert_to_flashcard_response(self, flashcard_doc: Dict) -> FlashcardResponse:
        """Convert flashcard document to response model."""
        from app.models.flashcard import FlashcardContent

        # Convert front and back content
        front_content = FlashcardContent(**flashcard_doc["front"])
        back_content = FlashcardContent(**flashcard_doc["back"])

        return FlashcardResponse(
            _id=str(flashcard_doc["_id"]),  # Use _id instead of id due to alias
            deck_id=flashcard_doc["deck_id"],
            front=front_content,
            back=back_content,
            hint=flashcard_doc.get("hint"),
            explanation=flashcard_doc.get("explanation"),
            difficulty_level=flashcard_doc["difficulty_level"],
            tags=flashcard_doc.get("tags", []),
            order_index=flashcard_doc.get("order_index", 0),
            created_by=flashcard_doc["created_by"],
            created_at=flashcard_doc["created_at"],
            updated_at=flashcard_doc["updated_at"],
            times_reviewed=flashcard_doc.get("times_reviewed", 0),
            last_reviewed=flashcard_doc.get("last_reviewed")
        )
