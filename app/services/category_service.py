"""
Category service for deck categorization with predefined categories.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.utils.database import db
from app.models.category import (
    CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse,
    CategoryListResponse, PREDEFINED_CATEGORIES
)
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for category management."""
    
    def __init__(self):
        self.db = db.database
        self.collection = self.db.categories
        self.decks_collection = self.db.decks
        self.users_collection = self.db.users
        
    async def get_categories(self) -> CategoryListResponse:
        """Get all categories with deck counts."""
        try:
            # Get all categories
            cursor = self.collection.find({}).sort("name", 1)
            categories = []
            
            async for category_doc in cursor:
                # Count decks in this category
                deck_count = await self.decks_collection.count_documents({
                    "category_id": str(category_doc["_id"])
                })
                
                category_response = await self._convert_to_category_response(
                    category_doc, deck_count
                )
                categories.append(category_response)
            
            # Count predefined vs custom
            predefined_count = sum(1 for cat in categories if cat.is_predefined)
            custom_count = len(categories) - predefined_count
            
            return CategoryListResponse(
                categories=categories,
                total_count=len(categories),
                predefined_count=predefined_count,
                custom_count=custom_count
            )
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            raise
    
    async def create_category(
        self,
        category_data: CategoryCreateRequest,
        creator_id: str
    ) -> CategoryResponse:
        """Create a new category (admin only)."""
        try:
            # Get creator info
            creator = await self.users_collection.find_one({"_id": ObjectId(creator_id)})
            if not creator:
                raise ValueError("Creator not found")
            
            # Check if creator is admin
            if creator.get("role") != UserRole.ADMIN:
                raise PermissionError("Only admins can create categories")
            
            # Check for duplicate name
            existing = await self.collection.find_one({
                "name": {"$regex": f"^{category_data.name}$", "$options": "i"}
            })
            if existing:
                raise ValueError(f"Category '{category_data.name}' already exists")
            
            # Prepare category document
            category_doc = {
                "name": category_data.name,
                "description": category_data.description,
                "icon": category_data.icon,
                "color": category_data.color,
                "is_predefined": False,  # Custom categories are never predefined
                "created_by": creator_id,
                "created_by_username": creator["username"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert category
            result = await self.collection.insert_one(category_doc)
            category_doc["_id"] = result.inserted_id
            
            # Convert to response
            category_response = await self._convert_to_category_response(category_doc, 0)
            
            logger.info(f"Created category {result.inserted_id} by admin {creator_id}")
            return category_response
            
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            raise
    
    async def update_category(
        self,
        category_id: str,
        category_data: CategoryUpdateRequest,
        updater_id: str
    ) -> Optional[CategoryResponse]:
        """Update category (admin only)."""
        try:
            # Get existing category
            category_doc = await self.collection.find_one({"_id": ObjectId(category_id)})
            if not category_doc:
                return None
            
            # Get updater info
            updater = await self.users_collection.find_one({"_id": ObjectId(updater_id)})
            if not updater:
                raise ValueError("Updater not found")
            
            # Check if updater is admin
            if updater.get("role") != UserRole.ADMIN:
                raise PermissionError("Only admins can update categories")
            
            # Check if trying to update predefined category name
            if category_doc.get("is_predefined") and category_data.name:
                raise PermissionError("Cannot change name of predefined categories")
            
            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}
            
            # Update fields that are provided
            for field, value in category_data.dict(exclude_unset=True).items():
                if value is not None:
                    # Check for duplicate name if updating name
                    if field == "name":
                        existing = await self.collection.find_one({
                            "_id": {"$ne": ObjectId(category_id)},
                            "name": {"$regex": f"^{value}$", "$options": "i"}
                        })
                        if existing:
                            raise ValueError(f"Category '{value}' already exists")
                    
                    update_data[field] = value
            
            # Update category
            await self.collection.update_one(
                {"_id": ObjectId(category_id)},
                {"$set": update_data}
            )
            
            # Get updated category
            updated_category = await self.collection.find_one({"_id": ObjectId(category_id)})
            
            # Get deck count
            deck_count = await self.decks_collection.count_documents({
                "category_id": category_id
            })
            
            category_response = await self._convert_to_category_response(
                updated_category, deck_count
            )
            
            logger.info(f"Updated category {category_id} by admin {updater_id}")
            return category_response
            
        except Exception as e:
            logger.error(f"Error updating category {category_id}: {str(e)}")
            raise
    
    async def delete_category(
        self,
        category_id: str,
        deleter_id: str
    ) -> bool:
        """Delete category (admin only)."""
        try:
            # Get existing category
            category_doc = await self.collection.find_one({"_id": ObjectId(category_id)})
            if not category_doc:
                return False
            
            # Get deleter info
            deleter = await self.users_collection.find_one({"_id": ObjectId(deleter_id)})
            if not deleter:
                raise ValueError("Deleter not found")
            
            # Check if deleter is admin
            if deleter.get("role") != UserRole.ADMIN:
                raise PermissionError("Only admins can delete categories")
            
            # Check if predefined category
            if category_doc.get("is_predefined"):
                raise PermissionError("Cannot delete predefined categories")
            
            # Check if category has decks
            deck_count = await self.decks_collection.count_documents({
                "category_id": category_id
            })
            if deck_count > 0:
                raise PermissionError(f"Cannot delete category with {deck_count} decks. Move decks first.")
            
            # Delete category
            result = await self.collection.delete_one({"_id": ObjectId(category_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted category {category_id} by admin {deleter_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {str(e)}")
            raise
    
    async def seed_predefined_categories(self) -> int:
        """Seed predefined categories into database."""
        try:
            seeded_count = 0
            
            for predefined_cat in PREDEFINED_CATEGORIES:
                # Check if category already exists
                existing = await self.collection.find_one({
                    "name": predefined_cat.name,
                    "is_predefined": True
                })
                
                if not existing:
                    # Create predefined category
                    category_doc = {
                        "name": predefined_cat.name,
                        "description": predefined_cat.description,
                        "icon": predefined_cat.icon,
                        "color": predefined_cat.color,
                        "is_predefined": True,
                        "created_by": None,
                        "created_by_username": "system",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    await self.collection.insert_one(category_doc)
                    seeded_count += 1
                    logger.info(f"Seeded predefined category: {predefined_cat.name}")
            
            logger.info(f"Seeded {seeded_count} predefined categories")
            return seeded_count
            
        except Exception as e:
            logger.error(f"Error seeding predefined categories: {str(e)}")
            raise
    
    async def _convert_to_category_response(
        self, 
        category_doc: Dict, 
        deck_count: int
    ) -> CategoryResponse:
        """Convert category document to response model."""
        return CategoryResponse(
            id=str(category_doc["_id"]),
            name=category_doc["name"],
            description=category_doc.get("description"),
            icon=category_doc.get("icon"),
            color=category_doc.get("color"),
            is_predefined=category_doc.get("is_predefined", False),
            deck_count=deck_count,
            created_at=category_doc["created_at"],
            updated_at=category_doc["updated_at"],
            created_by=category_doc.get("created_by"),
            created_by_username=category_doc.get("created_by_username")
        )
