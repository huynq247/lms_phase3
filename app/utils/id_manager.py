"""
Unified ID management strategy for consistent frontend-backend interaction
"""
from bson import ObjectId
from typing import Union, Optional
import re
from enum import Enum

class IDType(str, Enum):
    """Types of IDs in the system"""
    OBJECT_ID = "object_id"      # MongoDB ObjectId (24 hex chars)
    STRING_ID = "string_id"      # Custom string identifier
    UUID = "uuid"                # UUID format (future consideration)

class IDValidator:
    """Centralized ID validation and conversion"""
    
    # Regex patterns
    OBJECT_ID_PATTERN = re.compile(r'^[0-9a-fA-F]{24}$')
    STRING_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,100}$')
    UUID_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
    
    @classmethod
    def validate_object_id(cls, id_str: str) -> bool:
        """Validate MongoDB ObjectId format"""
        if not isinstance(id_str, str):
            return False
        return bool(cls.OBJECT_ID_PATTERN.match(id_str))
    
    @classmethod
    def validate_string_id(cls, id_str: str) -> bool:
        """Validate custom string ID format"""
        if not isinstance(id_str, str):
            return False
        return bool(cls.STRING_ID_PATTERN.match(id_str))
    
    @classmethod
    def detect_id_type(cls, id_str: str) -> Optional[IDType]:
        """Detect the type of ID"""
        if cls.validate_object_id(id_str):
            return IDType.OBJECT_ID
        elif cls.validate_string_id(id_str):
            return IDType.STRING_ID
        elif cls.UUID_PATTERN.match(id_str):
            return IDType.UUID
        return None
    
    @classmethod
    def convert_to_object_id(cls, id_str: str) -> ObjectId:
        """Convert string to ObjectId (with validation)"""
        if not cls.validate_object_id(id_str):
            raise ValueError(f"Invalid ObjectId format: {id_str}")
        return ObjectId(id_str)
    
    @classmethod
    def safe_object_id_convert(cls, id_input: Union[str, ObjectId]) -> ObjectId:
        """Safely convert various inputs to ObjectId"""
        if isinstance(id_input, ObjectId):
            return id_input
        elif isinstance(id_input, str):
            return cls.convert_to_object_id(id_input)
        else:
            raise ValueError(f"Cannot convert {type(id_input)} to ObjectId")

class IDManager:
    """Unified ID management for entities"""
    
    # Define which entities use which ID types
    ENTITY_ID_TYPES = {
        # Core entities (use ObjectId)
        "user": IDType.OBJECT_ID,
        "deck": IDType.OBJECT_ID,
        "flashcard": IDType.OBJECT_ID,
        "category": IDType.OBJECT_ID,
        "assignment": IDType.OBJECT_ID,
        
        # Assignment entities (use String IDs)
        "class": IDType.STRING_ID,
        "course": IDType.STRING_ID,
        "lesson": IDType.STRING_ID,
    }
    
    @classmethod
    def get_entity_id_type(cls, entity_name: str) -> IDType:
        """Get expected ID type for entity"""
        return cls.ENTITY_ID_TYPES.get(entity_name, IDType.OBJECT_ID)
    
    @classmethod
    def validate_entity_id(cls, entity_name: str, id_value: str) -> bool:
        """Validate ID for specific entity type"""
        expected_type = cls.get_entity_id_type(entity_name)
        detected_type = IDValidator.detect_id_type(id_value)
        return detected_type == expected_type
    
    @classmethod
    def format_id_for_frontend(cls, entity_name: str, id_value: Union[str, ObjectId]) -> str:
        """Format ID for frontend consumption"""
        # Always return string representation
        return str(id_value)
    
    @classmethod
    def prepare_id_for_database(cls, entity_name: str, id_value: str) -> Union[str, ObjectId]:
        """Prepare ID for database operations"""
        expected_type = cls.get_entity_id_type(entity_name)
        
        if expected_type == IDType.OBJECT_ID:
            return IDValidator.convert_to_object_id(id_value)
        else:
            return id_value  # Keep as string

# Example usage and validation
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("user", "6894d608ca395c993430a7f9", True),
        ("deck", "6894f7d942907590250f3fb9", True),
        ("class", "python_class_2024", True),
        ("course", "invalid-course-id!", False),  # Contains invalid chars
        ("user", "invalid_user_id", False),       # Not ObjectId format
    ]
    
    for entity, id_val, expected in test_cases:
        result = IDManager.validate_entity_id(entity, id_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} {entity}: {id_val} -> {result}")
