"""
Authentication service for user management and authentication.
"""
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.core.security import (
    verify_password, 
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    validate_password_strength,
    add_token_to_blacklist
)
from app.models.user import User, UserCreate
from app.models.enums import UserRole
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    UserTokenInfo
)


class AuthService:
    """Authentication service."""
    
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
    
    async def register_user(self, user_data: UserRegisterRequest) -> UserRegisterResponse:
        """Register a new user."""
        
        # Validate password strength
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements"
            )
        
        # Check if username already exists
        existing_user = await self.users_collection.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await self.users_collection.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user_create = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        # Hash password
        password_hash = get_password_hash(user_create.password)
        
        # Prepare user document
        user_doc = {
            "username": user_create.username,
            "email": user_create.email,
            "password_hash": password_hash,
            "role": user_create.role,
            "first_name": user_create.first_name,
            "last_name": user_create.last_name,
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "class_ids": []
        }
        
        # Insert user
        result = await self.users_collection.insert_one(user_doc)
        
        # Get created user
        created_user = await self.users_collection.find_one({"_id": result.inserted_id})
        
        return UserRegisterResponse(
            id=str(created_user["_id"]),
            username=created_user["username"],
            email=created_user["email"],
            role=created_user["role"],
            first_name=created_user.get("first_name"),
            last_name=created_user.get("last_name"),
            is_active=created_user["is_active"],
            created_at=created_user["created_at"]
        )
    
    async def authenticate_user(self, login_data: UserLoginRequest) -> TokenResponse:
        """Authenticate user and return tokens."""
        
        # Find user by email
        user_doc = await self.users_collection.find_one({"email": login_data.email})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user_doc["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user_doc["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Update last login
        await self.users_collection.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create tokens
        token_data = {"sub": str(user_doc["_id"]), "role": user_doc["role"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Create user info for token response
        user_info = UserTokenInfo(
            id=str(user_doc["_id"]),
            username=user_doc["username"],
            email=user_doc["email"],
            role=user_doc["role"],
            is_active=user_doc["is_active"]
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800,  # 30 minutes
            user=user_info
        )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        
        # Decode refresh token
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user_id = payload.get("sub")
        user_doc = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc or not user_doc["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {"sub": str(user_doc["_id"]), "role": user_doc["role"]}
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        # Create user info
        user_info = UserTokenInfo(
            id=str(user_doc["_id"]),
            username=user_doc["username"],
            email=user_doc["email"],
            role=user_doc["role"],
            is_active=user_doc["is_active"]
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=1800,  # 30 minutes
            user=user_info
        )
    
    async def logout_user(self, user_id: str) -> dict:
        """Logout user by blacklisting token."""
        # For now, we'll just log the logout action
        # In a real implementation, we'd blacklist the actual token
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_logout": datetime.utcnow()}}
        )
        
        return {"message": "Successfully logged out"}
    
    async def verify_email(self, token: str) -> dict:
        """Verify user email with verification token."""
        try:
            # In a real implementation, you'd decode the verification token
            # For now, we'll simulate email verification
            # decoded_token = decode_verification_token(token)
            # user_id = decoded_token.get("user_id")
            
            # For demo purposes, assume token is user_id
            if ObjectId.is_valid(token):
                result = await self.users_collection.update_one(
                    {"_id": ObjectId(token)},
                    {
                        "$set": {
                            "is_verified": True,
                            "email_verified_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    return {"message": "Email verified successfully"}
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            user_doc = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return User(**user_doc)
            return None
        except Exception:
            return None
    
    async def reset_user_password(self, user_id: str, new_password: str) -> dict:
        """Reset user password (admin function)."""
        
        # Validate password strength
        if not validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements"
            )
        
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Password reset successfully"}
