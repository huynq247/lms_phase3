"""
Admin service for user management operations.
"""
import math
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import User, UserRole
from app.models.admin import (
    UserListResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserPasswordResetResponse,
    AdminUserResponse,
    AdminAuditLog
)
from app.core.security import get_password_hash


class AdminService:
    """Service for admin user management operations."""
    
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
        self.audit_logs_collection = db.admin_audit_logs
    
    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> UserListResponse:
        """Get paginated list of users with filtering."""
        try:
            # Build query filter
            query_filter = {}
            
            # Search filter
            if search:
                query_filter["$or"] = [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"first_name": {"$regex": search, "$options": "i"}},
                    {"last_name": {"$regex": search, "$options": "i"}}
                ]
            
            # Role filter
            if role:
                query_filter["role"] = role.value
            
            # Active status filter
            if is_active is not None:
                query_filter["is_active"] = is_active
            
            # Get total count
            total_count = await self.users_collection.count_documents(query_filter)
            
            # Calculate pagination
            total_pages = math.ceil(total_count / limit)
            skip = (page - 1) * limit
            
            # Get users with pagination
            cursor = self.users_collection.find(query_filter).skip(skip).limit(limit)
            users_data = await cursor.to_list(length=limit)
            
            # Convert to response models
            users = []
            for user_data in users_data:
                user_data["_id"] = str(user_data["_id"])
                # Remove sensitive fields
                user_data.pop("password_hash", None)
                users.append(AdminUserResponse(**user_data))
            
            return UserListResponse(
                users=users,
                total=total_count,  # Add total field
                total_count=total_count,
                page=page,
                limit=limit,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1
            )
            
        except Exception as e:
            print(f"Error getting users: {e}")
            return UserListResponse(
                users=[],
                total=0,  # Add total field
                total_count=0,
                page=page,
                limit=limit,
                total_pages=0,
                has_next=False,
                has_prev=False
            )
    
    async def create_user(
        self, 
        user_data: UserCreateRequest, 
        admin_id: str
    ) -> Optional[UserCreateResponse]:
        """Create a new user account."""
        try:
            # Check if username or email already exists
            existing_user = await self.users_collection.find_one({
                "$or": [
                    {"username": user_data.username},
                    {"email": user_data.email}
                ]
            })
            
            if existing_user:
                return None
            
            # Hash password
            password_hash = get_password_hash(user_data.password)
            
            # Create user document
            new_user = {
                "username": user_data.username,
                "email": user_data.email,
                "password_hash": password_hash,
                "role": user_data.role.value,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "is_active": user_data.is_active,
                "is_verified": True,  # Admin-created users are auto-verified
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "class_ids": [],
                # Extended profile fields with defaults
                "learning_preferences": None,
                "learning_goals": [],
                "study_schedule": [],
                "achievements": [],
                "study_statistics": {
                    "total_study_time_minutes": 0,
                    "total_cards_studied": 0,
                    "total_decks_created": 0,
                    "current_streak_days": 0,
                    "longest_streak_days": 0,
                    "accuracy_percentage": 0.0,
                    "last_study_date": None
                }
            }
            
            # Insert user
            result = await self.users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)
            
            # Log admin action
            await self._log_admin_action(
                admin_id=admin_id,
                action="create_user",
                target_user_id=user_id,
                target_username=user_data.username,
                details={
                    "role": user_data.role.value,
                    "is_active": user_data.is_active,
                    "email": user_data.email
                }
            )
            
            return UserCreateResponse(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                role=user_data.role,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_active=user_data.is_active,
                created_at=new_user["created_at"],
                created_by=admin_id
            )
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    async def reset_user_password(
        self,
        user_id: str,
        new_password: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> Optional[UserPasswordResetResponse]:
        """Reset user password."""
        try:
            # Get target user
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return None
            
            # Hash new password
            password_hash = get_password_hash(new_password)
            
            # Update password
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                return None
            
            # Log admin action
            await self._log_admin_action(
                admin_id=admin_id,
                action="reset_password",
                target_user_id=user_id,
                target_username=user["username"],
                details={"password_changed": True},
                reason=reason
            )
            
            return UserPasswordResetResponse(
                user_id=user_id,
                username=user["username"],
                email=user["email"],
                reset_at=datetime.utcnow(),
                reset_by=admin_id,
                reason=reason
            )
            
        except Exception as e:
            print(f"Error resetting password: {e}")
            return None
    
    async def update_user_role(
        self,
        user_id: str,
        new_role: UserRole,
        admin_id: str,
        reason: Optional[str] = None
    ) -> Optional[AdminUserResponse]:
        """Update user role."""
        try:
            # Get target user
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return None
            
            old_role = user.get("role")
            
            # Update role
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "role": new_role.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                return None
            
            # Log admin action
            await self._log_admin_action(
                admin_id=admin_id,
                action="update_role",
                target_user_id=user_id,
                target_username=user["username"],
                details={
                    "old_role": old_role,
                    "new_role": new_role.value
                },
                reason=reason
            )
            
            # Get updated user
            updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            updated_user["_id"] = str(updated_user["_id"])
            updated_user.pop("password_hash", None)
            
            return AdminUserResponse(**updated_user)
            
        except Exception as e:
            print(f"Error updating user role: {e}")
            return None
    
    async def deactivate_user(
        self,
        user_id: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Deactivate user account."""
        try:
            # Get target user
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return False
            
            # Deactivate user
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                return False
            
            # Log admin action
            await self._log_admin_action(
                admin_id=admin_id,
                action="deactivate_user",
                target_user_id=user_id,
                target_username=user["username"],
                details={"deactivated": True},
                reason=reason
            )
            
            return True
            
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False
    
    async def _log_admin_action(
        self,
        admin_id: str,
        action: str,
        target_user_id: str,
        target_username: str,
        details: Dict[str, Any],
        reason: Optional[str] = None
    ):
        """Log admin action for audit trail."""
        try:
            # Get admin info
            admin = await self.users_collection.find_one({"_id": ObjectId(admin_id)})
            admin_username = admin["username"] if admin else "unknown"
            
            # Create audit log entry
            audit_log = {
                "admin_id": admin_id,
                "admin_username": admin_username,
                "action": action,
                "target_user_id": target_user_id,
                "target_username": target_username,
                "details": details,
                "reason": reason,
                "timestamp": datetime.utcnow(),
                "ip_address": None  # Could be extracted from request context
            }
            
            await self.audit_logs_collection.insert_one(audit_log)
            
        except Exception as e:
            print(f"Error logging admin action: {e}")
            # Don't fail the main operation if logging fails
