"""
Deck service with advanced privacy features and access control.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from app.utils.database import db
from app.models.deck import (
    DeckCreateRequest, DeckUpdateRequest, DeckResponse, 
    DeckListResponse, DeckAccessInfo, DeckPrivacyLevel
)
from app.models.user import User
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class DeckService:
    """Service for deck management with advanced privacy features."""
    
    def __init__(self):
        self.db = db.database
        self.collection = self.db.decks
        self.users_collection = self.db.users
        
    async def get_user_accessible_decks(
        self,
        current_user_id: str,
        page: int = 1,
        limit: int = 10,
        privacy_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        difficulty_filter: Optional[str] = None,
        owner_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> DeckListResponse:
        """
        Get decks accessible to current user with privacy filtering.
        
        Privacy Access Rules:
        1. Owner: Can access all their own decks
        2. Admin: Can access all decks
        3. Teacher: Can access public + their assigned decks
        4. Student: Can access public + their assigned decks
        """
        try:
            # Get current user info
            current_user = await self._get_user_by_id(current_user_id)
            if not current_user:
                raise ValueError("User not found")
            
            # DEBUG: Log parameters
            logger.info(f"DeckService.get_user_accessible_decks called with privacy_filter: {privacy_filter}")
            
            # Build privacy filter
            privacy_conditions = await self._build_privacy_filter(current_user)
            
            # Build query conditions
            query_conditions = []
            
            # Add privacy conditions (unless admin with explicit privacy filter)
            user_role = current_user.get("role", UserRole.STUDENT)
            if user_role == UserRole.ADMIN and privacy_filter:
                # Admin with explicit privacy filter - only apply that filter
                query_conditions.append({"privacy_level": privacy_filter})
            elif user_role != UserRole.ADMIN and privacy_filter:
                # Non-admin with privacy filter: intersect accessibility with filter
                if privacy_conditions:
                    # Combine privacy access rules with specific privacy filter
                    query_conditions.append({
                        "$and": [
                            privacy_conditions,
                            {"privacy_level": privacy_filter}
                        ]
                    })
                else:
                    # Fallback to just privacy filter
                    query_conditions.append({"privacy_level": privacy_filter})
            elif privacy_conditions:
                # Regular privacy filtering without specific filter
                query_conditions.append(privacy_conditions)
            
            # Build additional filters
            applied_filters = {}
            
            # Track privacy filter in applied_filters
            if privacy_filter:
                applied_filters["privacy_level"] = privacy_filter
            
            # Tags filter
            if tags_filter:
                query_conditions.append({"tags": {"$in": tags_filter}})
                applied_filters["tags"] = tags_filter
            
            # Difficulty filter
            if difficulty_filter:
                query_conditions.append({"difficulty_level": difficulty_filter})
                applied_filters["difficulty_level"] = difficulty_filter
            
            # Owner filter
            if owner_filter:
                query_conditions.append({"owner_id": owner_filter})
                applied_filters["owner"] = owner_filter
            
            # Category filter
            if category_id:
                query_conditions.append({"category_id": category_id})
                applied_filters["category_id"] = category_id
            
            # Search query (title + description)
            if search_query:
                search_regex = {"$regex": search_query, "$options": "i"}
                query_conditions.append({
                    "$or": [
                        {"title": search_regex},
                        {"description": search_regex}
                    ]
                })
                applied_filters["search"] = search_query
            
            # Build final query
            if query_conditions:
                query = {"$and": query_conditions}
            else:
                query = {}
            
            # Count total
            total_count = await self.collection.count_documents(query)
            
            # Get decks with pagination
            skip = (page - 1) * limit
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("updated_at", -1)
            
            decks = []
            async for deck_doc in cursor:
                deck_response = await self._convert_to_deck_response(deck_doc, current_user)
                decks.append(deck_response)
            
            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return DeckListResponse(
                decks=decks,
                total_count=total_count,
                page=page,
                limit=limit,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
                applied_filters=applied_filters
            )
            
        except Exception as e:
            logger.error(f"Error getting user accessible decks: {str(e)}")
            raise
    
    async def create_deck(
        self,
        deck_data: DeckCreateRequest,
        owner_id: str
    ) -> DeckResponse:
        """Create a new deck with owner validation."""
        try:
            # Get owner info
            owner = await self._get_user_by_id(owner_id)
            if not owner:
                raise ValueError("Owner not found")
            
            # Validate assignment permissions
            await self._validate_assignment_permissions(owner, deck_data)
            
            # Prepare deck document
            deck_doc = {
                "title": deck_data.title,
                "description": deck_data.description,
                "category_id": deck_data.category_id,
                "privacy_level": deck_data.privacy_level,
                "tags": deck_data.tags,
                "difficulty_level": deck_data.difficulty_level,
                "estimated_time_minutes": deck_data.estimated_time_minutes,
                "owner_id": owner_id,
                "owner_username": owner["username"],
                "assigned_class_ids": deck_data.assigned_class_ids or [],
                "assigned_course_ids": deck_data.assigned_course_ids or [],
                "assigned_lesson_ids": deck_data.assigned_lesson_ids or [],
                "total_cards": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert deck
            result = await self.collection.insert_one(deck_doc)
            deck_doc["_id"] = result.inserted_id
            
            # Convert to response
            deck_response = await self._convert_to_deck_response(deck_doc, owner)
            
            logger.info(f"Created deck {result.inserted_id} by user {owner_id}")
            return deck_response
            
        except Exception as e:
            logger.error(f"Error creating deck: {str(e)}")
            raise
    
    async def get_deck_by_id(
        self,
        deck_id: str,
        current_user_id: str
    ) -> Optional[DeckResponse]:
        """Get deck by ID with access validation."""
        try:
            # Get deck
            deck_doc = await self.collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                return None
            
            # Get current user
            current_user = await self._get_user_by_id(current_user_id)
            if not current_user:
                raise ValueError("User not found")
            
            # Check access permissions
            access_info = await self._check_deck_access(deck_doc, current_user)
            if not access_info.can_view:
                return None  # User cannot access this deck
            
            # Convert to response
            deck_response = await self._convert_to_deck_response(deck_doc, current_user)
            return deck_response
            
        except Exception as e:
            logger.error(f"Error getting deck {deck_id}: {str(e)}")
            raise
    
    async def update_deck(
        self,
        deck_id: str,
        deck_data: DeckUpdateRequest,
        current_user_id: str
    ) -> Optional[DeckResponse]:
        """Update deck with owner validation."""
        try:
            # Get existing deck
            deck_doc = await self.collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                return None
            
            # Get current user
            current_user = await self._get_user_by_id(current_user_id)
            if not current_user:
                raise ValueError("User not found")
            
            # Check edit permissions
            access_info = await self._check_deck_access(deck_doc, current_user)
            if not access_info.can_edit:
                raise PermissionError("You don't have permission to edit this deck")
            
            # Validate assignment permissions if privacy/assignments are changing
            if (deck_data.privacy_level or 
                deck_data.assigned_class_ids is not None or
                deck_data.assigned_course_ids is not None or
                deck_data.assigned_lesson_ids is not None):
                await self._validate_assignment_permissions(current_user, deck_data)
            
            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}
            
            # Update fields that are provided
            for field, value in deck_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            # Update deck
            await self.collection.update_one(
                {"_id": ObjectId(deck_id)},
                {"$set": update_data}
            )
            
            # Get updated deck
            updated_deck = await self.collection.find_one({"_id": ObjectId(deck_id)})
            deck_response = await self._convert_to_deck_response(updated_deck, current_user)
            
            logger.info(f"Updated deck {deck_id} by user {current_user_id}")
            return deck_response
            
        except Exception as e:
            logger.error(f"Error updating deck {deck_id}: {str(e)}")
            raise
    
    async def delete_deck(
        self,
        deck_id: str,
        current_user_id: str
    ) -> bool:
        """Delete deck with owner validation."""
        try:
            # Get existing deck
            deck_doc = await self.collection.find_one({"_id": ObjectId(deck_id)})
            if not deck_doc:
                return False
            
            # Get current user
            current_user = await self._get_user_by_id(current_user_id)
            if not current_user:
                raise ValueError("User not found")
            
            # Check delete permissions
            access_info = await self._check_deck_access(deck_doc, current_user)
            if not access_info.can_delete:
                raise PermissionError("You don't have permission to delete this deck")
            
            # Delete deck
            result = await self.collection.delete_one({"_id": ObjectId(deck_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted deck {deck_id} by user {current_user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting deck {deck_id}: {str(e)}")
            raise
    
    async def _get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        try:
            return await self.users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
    
    async def _build_privacy_filter(self, current_user: Dict) -> Dict:
        """Build privacy filter based on user role and assignments."""
        user_id = str(current_user["_id"])
        user_role = current_user.get("role", UserRole.STUDENT)
        
        # Admin can see all decks
        if user_role == UserRole.ADMIN:
            return {}  # No restrictions
        
        # Owner can see their own decks
        owner_condition = {"owner_id": user_id}
        
        # Everyone can see public decks
        public_condition = {"privacy_level": DeckPrivacyLevel.PUBLIC}
        
        # Build assignment conditions based on user's assignments
        assignment_conditions = []
        
        # Get user's class assignments
        user_class_ids = current_user.get("class_ids", [])
        if user_class_ids:
            assignment_conditions.append({
                "privacy_level": DeckPrivacyLevel.CLASS_ASSIGNED,
                "assigned_class_ids": {"$in": user_class_ids}
            })
        
        # Get user's course assignments
        user_course_ids = current_user.get("course_ids", [])
        if user_course_ids:
            assignment_conditions.append({
                "privacy_level": DeckPrivacyLevel.COURSE_ASSIGNED,
                "assigned_course_ids": {"$in": user_course_ids}
            })
        
        # Get user's lesson assignments
        user_lesson_ids = current_user.get("lesson_ids", [])
        if user_lesson_ids:
            assignment_conditions.append({
                "privacy_level": DeckPrivacyLevel.LESSON_ASSIGNED,
                "assigned_lesson_ids": {"$in": user_lesson_ids}
            })
        
        # Combine all conditions with OR
        all_conditions = [owner_condition, public_condition] + assignment_conditions
        
        return {"$or": all_conditions}
    
    async def _check_deck_access(self, deck_doc: Dict, current_user: Dict) -> DeckAccessInfo:
        """Check user's access permissions for a deck."""
        user_id = str(current_user["_id"])
        user_role = current_user.get("role", UserRole.STUDENT)
        deck_owner_id = deck_doc.get("owner_id")
        deck_privacy = deck_doc.get("privacy_level")
        
        # Initialize access info
        can_view = False
        can_edit = False
        can_delete = False
        access_reason = "no_access"
        
        # Admin has full access to all decks
        if user_role == UserRole.ADMIN:
            can_view = True
            can_edit = True
            can_delete = True
            access_reason = "admin"
        
        # Owner has full access to their own decks
        elif deck_owner_id == user_id:
            can_view = True
            can_edit = True
            can_delete = True
            access_reason = "owner"
        
        # Public decks are viewable by everyone
        elif deck_privacy == DeckPrivacyLevel.PUBLIC:
            can_view = True
            access_reason = "public"
        
        # Check assignment-based access
        else:
            access_reason = await self._check_assignment_access(deck_doc, current_user)
            if access_reason != "no_access":
                can_view = True
        
        return DeckAccessInfo(
            can_view=can_view,
            can_edit=can_edit,
            can_delete=can_delete,
            access_reason=access_reason
        )
    
    async def _check_assignment_access(self, deck_doc: Dict, current_user: Dict) -> str:
        """Check if user has assignment-based access to deck."""
        deck_privacy = deck_doc.get("privacy_level")
        
        # Check class assignment
        if deck_privacy == DeckPrivacyLevel.CLASS_ASSIGNED:
            user_class_ids = current_user.get("class_ids", [])
            deck_class_ids = deck_doc.get("assigned_class_ids", [])
            if any(class_id in deck_class_ids for class_id in user_class_ids):
                return "class_assigned"
        
        # Check course assignment
        elif deck_privacy == DeckPrivacyLevel.COURSE_ASSIGNED:
            user_course_ids = current_user.get("course_ids", [])
            deck_course_ids = deck_doc.get("assigned_course_ids", [])
            if any(course_id in deck_course_ids for course_id in user_course_ids):
                return "course_assigned"
        
        # Check lesson assignment
        elif deck_privacy == DeckPrivacyLevel.LESSON_ASSIGNED:
            user_lesson_ids = current_user.get("lesson_ids", [])
            deck_lesson_ids = deck_doc.get("assigned_lesson_ids", [])
            if any(lesson_id in deck_lesson_ids for lesson_id in user_lesson_ids):
                return "lesson_assigned"
        
        return "no_access"
    
    async def _validate_assignment_permissions(self, user: Dict, deck_data) -> None:
        """Validate user has permission to make assignments."""
        user_role = user.get("role", UserRole.STUDENT)
        
        # Students cannot create assigned decks
        if user_role == UserRole.STUDENT:
            if (deck_data.privacy_level in [
                DeckPrivacyLevel.CLASS_ASSIGNED,
                DeckPrivacyLevel.COURSE_ASSIGNED,
                DeckPrivacyLevel.LESSON_ASSIGNED
            ]):
                raise PermissionError("Students cannot create assigned decks")
        
        # Teachers can only assign to their own classes/courses/lessons
        # (This would require additional validation based on your assignment system)
        # For now, we'll allow teachers to make assignments
        
    async def _convert_to_deck_response(self, deck_doc: Dict, current_user: Dict) -> DeckResponse:
        """Convert deck document to response model."""
        # Check access info
        access_info = await self._check_deck_access(deck_doc, current_user)
        
    async def _convert_to_deck_response(self, deck_doc: Dict, current_user: Dict) -> DeckResponse:
        """Convert deck document to response model."""
        # Check access info
        access_info = await self._check_deck_access(deck_doc, current_user)
        
        # Get category name if category_id exists
        category_name = None
        if deck_doc.get("category_id"):
            try:
                category_doc = await self.db.categories.find_one({
                    "_id": ObjectId(deck_doc["category_id"])
                })
                if category_doc:
                    category_name = category_doc["name"]
            except Exception:
                # If category not found or invalid ObjectId, ignore
                pass
        
        return DeckResponse(
            id=str(deck_doc["_id"]),
            title=deck_doc["title"],
            description=deck_doc.get("description"),
            category_id=deck_doc.get("category_id"),
            category_name=category_name,
            privacy_level=deck_doc["privacy_level"],
            tags=deck_doc.get("tags", []),
            difficulty_level=deck_doc.get("difficulty_level"),
            estimated_time_minutes=deck_doc.get("estimated_time_minutes"),
            owner_id=deck_doc["owner_id"],
            owner_username=deck_doc["owner_username"],
            assigned_class_ids=deck_doc.get("assigned_class_ids", []),
            assigned_course_ids=deck_doc.get("assigned_course_ids", []),
            assigned_lesson_ids=deck_doc.get("assigned_lesson_ids", []),
            total_cards=deck_doc.get("total_cards", 0),
            is_favorite=False,  # TODO: Implement user favorites
            can_edit=access_info.can_edit,
            created_at=deck_doc["created_at"],
            updated_at=deck_doc["updated_at"]
        )
