"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorDatabase
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.utils.database import get_database
from app.utils.response_standardizer import ResponseStandardizer
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    LogoutResponse
)
from app.core.deps import get_current_user
from app.models.user import User


# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterRequest,
    db = Depends(get_database)
):
    """Register a new user."""
    auth_service = AuthService(db)
    result = await auth_service.register_user(user_data)
    
    # Standardize response format (_id -> id)
    result_dict = jsonable_encoder(result)
    return ResponseStandardizer.create_standardized_response(result_dict, status_code=status.HTTP_201_CREATED)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Rate limit: 5 login attempts per minute
async def login_user(
    request: Request,
    login_data: UserLoginRequest,
    db = Depends(get_database)
):
    """Authenticate user and return access token."""
    auth_service = AuthService(db)
    result = await auth_service.authenticate_user(login_data)
    
    # Standardize response format (_id -> id)
    result_dict = jsonable_encoder(result)
    return ResponseStandardizer.create_standardized_response(result_dict)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefreshRequest,
    db = Depends(get_database)
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)
    result = await auth_service.refresh_token(token_data.refresh_token)
    
    # Standardize response format (_id -> id)
    result_dict = jsonable_encoder(result)
    return ResponseStandardizer.create_standardized_response(result_dict)


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Logout current user by blacklisting token."""
    auth_service = AuthService(db)
    result = await auth_service.logout_user(str(current_user.id))
    
    # Standardize response format (_id -> id)
    result_dict = jsonable_encoder(result)
    return ResponseStandardizer.create_standardized_response(result_dict)


@router.post("/verify-email")
async def verify_email(
    token: str,
    db = Depends(get_database)
):
    """Verify user email with verification token."""
    auth_service = AuthService(db)
    result = await auth_service.verify_email(token)
    
    # Standardize response format (_id -> id)
    result_dict = jsonable_encoder(result)
    return ResponseStandardizer.create_standardized_response(result_dict)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return current_user


@router.get("/verify")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role
    }
