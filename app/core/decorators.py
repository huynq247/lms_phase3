"""
Authorization decorators for role-based access control.
"""
from functools import wraps
from typing import List, Union
from fastapi import HTTPException, status
from app.models.enums import UserRole
from app.models.user import User


def require_role(required_roles: Union[UserRole, List[UserRole]]):
    """
    Decorator to require specific user roles for endpoint access.
    
    Args:
        required_roles: Single role or list of roles that can access the endpoint
        
    Usage:
        @require_role(UserRole.ADMIN)
        @require_role([UserRole.ADMIN, UserRole.TEACHER])
    """
    if isinstance(required_roles, UserRole):
        required_roles = [required_roles]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[role.value for role in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(permission: str):
    """
    Decorator to require specific permissions for endpoint access.
    
    Args:
        permission: Permission string required for access
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permission based on role
            role_permissions = {
                UserRole.ADMIN: [
                    "manage_users", "manage_courses", "manage_decks", 
                    "view_analytics", "system_admin"
                ],
                UserRole.TEACHER: [
                    "manage_classes", "manage_assignments", "view_student_progress",
                    "create_decks", "manage_own_content"
                ],
                UserRole.STUDENT: [
                    "study_decks", "create_own_decks", "join_classes", "view_own_progress"
                ]
            }
            
            user_permissions = role_permissions.get(current_user.role, [])
            
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {permission}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_ownership(resource_type: str):
    """
    Decorator to require resource ownership for endpoint access.
    
    Args:
        resource_type: Type of resource (deck, class, assignment, etc.)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need to be implemented based on specific resource checking logic
            # For now, just pass through - can be expanded later
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
