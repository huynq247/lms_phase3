"""
Enumeration classes for the application.
"""
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class Permission(str, Enum):
    """System permissions."""
    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Class Management
    CREATE_CLASS = "create_class"
    READ_CLASS = "read_class"
    UPDATE_CLASS = "update_class"
    DELETE_CLASS = "delete_class"
    MANAGE_CLASS_MEMBERS = "manage_class_members"
    
    # Course Management
    CREATE_COURSE = "create_course"
    READ_COURSE = "read_course"
    UPDATE_COURSE = "update_course"
    DELETE_COURSE = "delete_course"
    
    # Deck Management
    CREATE_DECK = "create_deck"
    READ_DECK = "read_deck"
    UPDATE_DECK = "update_deck"
    DELETE_DECK = "delete_deck"
    
    # Flashcard Management
    CREATE_FLASHCARD = "create_flashcard"
    READ_FLASHCARD = "read_flashcard"
    UPDATE_FLASHCARD = "update_flashcard"
    DELETE_FLASHCARD = "delete_flashcard"
    
    # Study Session
    START_STUDY_SESSION = "start_study_session"
    UPDATE_STUDY_PROGRESS = "update_study_progress"
    
    # Admin Functions
    RESET_PASSWORD = "reset_password"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SYSTEM = "manage_system"


class DeckPrivacyLevel(str, Enum):
    """Deck privacy levels."""
    PRIVATE = "private"              # Only owner can see
    CLASS_ONLY = "class_only"        # Only class members can see
    SCHOOL_WIDE = "school_wide"      # All users in school can see
    PUBLIC_READONLY = "public_readonly"  # Anyone can see, only owner can edit
    PUBLIC = "public"                # Anyone can see and copy


class StudyMode(str, Enum):
    """Study session modes."""
    REVIEW = "review"        # Spaced repetition review
    PRACTICE = "practice"    # Practice mode
    CRAM = "cram"           # Rapid review
    TEST = "test"           # Test mode
    LEARN = "learn"         # Learning new cards


class StudySessionStatus(str, Enum):
    """Study session status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
