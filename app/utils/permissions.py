from enum import Enum
from typing import List

class UserRole(str, Enum):
    """User roles enum."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class StudyMode(str, Enum):
    """Study modes enum."""
    REVIEW = "review"
    PRACTICE = "practice"
    CRAM = "cram"
    TEST = "test"
    LEARN = "learn"

class DifficultyLevel(str, Enum):
    """Difficulty levels for flashcards."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class PermissionLevel(str, Enum):
    """Permission levels for resources."""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"

def check_user_permission(user_role: str, required_role: str) -> bool:
    """Check if user has required permission level."""
    role_hierarchy = {
        UserRole.ADMIN: 3,
        UserRole.TEACHER: 2,
        UserRole.STUDENT: 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def can_access_resource(user_role: str, resource_owner_id: str, user_id: str, 
                       permission_level: str) -> bool:
    """Check if user can access a resource based on permission level."""
    
    # Admin can access everything
    if user_role == UserRole.ADMIN:
        return True
    
    # Owner can always access their own resources
    if resource_owner_id == user_id:
        return True
    
    # Check permission level
    if permission_level == PermissionLevel.PUBLIC:
        return True
    elif permission_level == PermissionLevel.SHARED:
        # Teachers can access shared resources
        return user_role in [UserRole.TEACHER, UserRole.ADMIN]
    else:  # PRIVATE
        return False

def get_allowed_roles_for_permission(permission_level: str) -> List[str]:
    """Get list of roles that can access a resource with given permission level."""
    if permission_level == PermissionLevel.PUBLIC:
        return [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]
    elif permission_level == PermissionLevel.SHARED:
        return [UserRole.TEACHER, UserRole.ADMIN]
    else:  # PRIVATE
        return []  # Only owner can access
