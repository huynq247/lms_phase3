"""
Admin user management endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.core.deps import get_current_user
from app.utils.database import get_database
from app.models.user import User, UserRole
from app.models.admin import (
    UserListResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserUpdateRoleRequest,
    UserPasswordResetRequest,
    UserPasswordResetResponse,
    AdminUserResponse
)
from app.services.admin_service import AdminService
from app.core.decorators import require_role

router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.get("/users", response_model=UserListResponse)
@require_role(UserRole.ADMIN)
async def get_users(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    Get list of users with pagination and filtering.
    
    Admin only endpoint for user management.
    
    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 10, max: 100)
        search: Search term for username or email
        role: Filter by user role
        is_active: Filter by active status
        
    Returns:
        UserListResponse: Paginated list of users
    """
    try:
        db = await get_database()
        admin_service = AdminService(db)
        
        users_data = await admin_service.get_users(
            page=page,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active
        )
        
        return users_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.post("/users", response_model=UserCreateResponse)
@require_role(UserRole.ADMIN)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user account.
    
    Admin only endpoint for user creation.
    
    Args:
        user_data: User creation data including role assignment
        
    Returns:
        UserCreateResponse: Created user information
    """
    try:
        db = await get_database()
        admin_service = AdminService(db)
        
        created_user = await admin_service.create_user(user_data, str(current_user.id))
        
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user. Username or email may already exist."
            )
        
        return created_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.put("/users/{user_id}/reset-password", response_model=UserPasswordResetResponse)
@require_role(UserRole.ADMIN)
async def reset_user_password(
    user_id: str,
    reset_data: UserPasswordResetRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Reset user password.
    
    Admin only endpoint for password management.
    
    Args:
        user_id: Target user ID
        reset_data: New password data
        
    Returns:
        UserPasswordResetResponse: Password reset confirmation
    """
    try:
        # Validate user_id format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        db = await get_database()
        admin_service = AdminService(db)
        
        reset_result = await admin_service.reset_user_password(
            user_id=user_id,
            new_password=reset_data.new_password,
            admin_id=str(current_user.id),
            reason=reset_data.reason
        )
        
        if not reset_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return reset_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
@require_role(UserRole.ADMIN)
async def update_user_role(
    user_id: str,
    role_data: UserUpdateRoleRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update user role.
    
    Admin only endpoint for role management.
    
    Args:
        user_id: Target user ID
        role_data: New role assignment
        
    Returns:
        AdminUserResponse: Updated user information
    """
    try:
        # Validate user_id format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Prevent admin from changing their own role
        if user_id == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role"
            )
        
        db = await get_database()
        admin_service = AdminService(db)
        
        updated_user = await admin_service.update_user_role(
            user_id=user_id,
            new_role=role_data.role,
            admin_id=str(current_user.id),
            reason=role_data.reason
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}"
        )


@router.delete("/users/{user_id}")
@require_role(UserRole.ADMIN)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    reason: Optional[str] = Query(None, description="Reason for deactivation")
):
    """
    Deactivate user account.
    
    Admin only endpoint for user deactivation.
    Note: Users are deactivated, not permanently deleted.
    
    Args:
        user_id: Target user ID
        reason: Reason for deactivation
        
    Returns:
        Success message
    """
    try:
        # Validate user_id format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Prevent admin from deactivating themselves
        if user_id == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        db = await get_database()
        admin_service = AdminService(db)
        
        success = await admin_service.deactivate_user(
            user_id=user_id,
            admin_id=str(current_user.id),
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "message": "User deactivated successfully",
            "user_id": user_id,
            "deactivated_by": str(current_user.id),
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )
