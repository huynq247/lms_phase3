"""
Authentication schemas for request/response models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


"""
Authentication schemas for request/response models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.enums import UserRole


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "student123",
                "email": "student@example.com",
                "password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    )


class UserRegisterResponse(BaseModel):
    """Response schema for user registration."""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    message: str = "User registered successfully"


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "student@example.com",
                "password": "SecurePassword123!"
            }
        }
    )


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserTokenInfo"


class UserTokenInfo(BaseModel):
    """User information included in token response."""
    id: str
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool


class TokenRefreshRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Request schema for password reset."""
    new_password: str = Field(..., min_length=8)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_password": "NewSecurePassword123!"
            }
        }
    )


class PasswordChangeRequest(BaseModel):
    """Request schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!"
            }
        }
    )


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    message: str = "Successfully logged out"
    logged_out_at: datetime = Field(default_factory=datetime.utcnow)


# Update forward references
TokenResponse.model_rebuild()
