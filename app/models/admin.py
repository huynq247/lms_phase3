"""
Admin management model definitions.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.models.enums import UserRole


class AdminUserResponse(BaseModel):
    """Admin view of user information."""
    id: str = Field(alias="_id")
    username: str
    email: EmailStr
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[AdminUserResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "username": "john_doe",
                        "email": "john@example.com",
                        "role": "student",
                        "is_active": True,
                        "is_verified": True
                    }
                ],
                "total_count": 50,
                "page": 1,
                "limit": 10,
                "total_pages": 5,
                "has_next": True,
                "has_prev": False
            }
        }


class UserCreateRequest(BaseModel):
    """Request to create a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.STUDENT
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "new_student",
                "email": "student@example.com",
                "password": "SecurePass123!",
                "role": "student",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True
            }
        }


class UserCreateResponse(BaseModel):
    """Response after creating a user."""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    created_by: str  # Admin ID who created this user
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "new_student",
                "email": "student@example.com",
                "role": "student",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "created_by": "507f1f77bcf86cd799439012"
            }
        }


class UserPasswordResetRequest(BaseModel):
    """Request to reset user password."""
    new_password: str = Field(..., min_length=8)
    reason: Optional[str] = Field(None, max_length=500, description="Reason for password reset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_password": "NewSecurePass123!",
                "reason": "User forgot password and requested reset"
            }
        }


class UserPasswordResetResponse(BaseModel):
    """Response after password reset."""
    user_id: str
    username: str
    email: EmailStr
    reset_at: datetime
    reset_by: str  # Admin ID who performed the reset
    reason: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "reset_at": "2024-01-15T10:30:00",
                "reset_by": "507f1f77bcf86cd799439012",
                "reason": "User forgot password and requested reset"
            }
        }


class UserUpdateRoleRequest(BaseModel):
    """Request to update user role."""
    role: UserRole
    reason: Optional[str] = Field(None, max_length=500, description="Reason for role change")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "teacher",
                "reason": "User is now qualified to teach classes"
            }
        }


class AdminAuditLog(BaseModel):
    """Admin action audit log entry."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    admin_id: str
    admin_username: str
    action: str  # create_user, reset_password, update_role, deactivate_user
    target_user_id: str
    target_username: str
    details: dict
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "admin_id": "507f1f77bcf86cd799439012",
                "admin_username": "admin_user",
                "action": "reset_password",
                "target_user_id": "507f1f77bcf86cd799439011",
                "target_username": "john_doe",
                "details": {"password_changed": True},
                "reason": "User forgot password",
                "timestamp": "2024-01-15T10:30:00",
                "ip_address": "192.168.1.100"
            }
        }
