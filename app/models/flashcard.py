"""
Flashcard models for multimedia content management.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class FlashcardContent(BaseModel):
    """Content structure for flashcard sides."""
    text: str = Field(..., description="Main text content")
    rich_text: Optional[Dict[str, Any]] = Field(None, description="Rich text formatting data")
    image_url: Optional[str] = Field(None, description="Image URL")
    audio_url: Optional[str] = Field(None, description="Audio URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "What is Python?",
                "rich_text": {
                    "format": "html",
                    "content": "<p><strong>What</strong> is <em>Python</em>?</p>"
                },
                "image_url": "/uploads/images/python_logo.png",
                "audio_url": "/uploads/audio/pronunciation.mp3"
            }
        }


class FlashcardBase(BaseModel):
    """Base flashcard fields."""
    front: FlashcardContent = Field(..., description="Front side content")
    back: FlashcardContent = Field(..., description="Back side content")
    hint: Optional[str] = Field(None, max_length=500, description="Optional hint")
    explanation: Optional[str] = Field(None, max_length=1000, description="Detailed explanation")
    difficulty_level: Optional[str] = Field(
        "medium", 
        pattern="^(easy|medium|hard)$",
        description="Flashcard difficulty"
    )
    tags: List[str] = Field(default_factory=list, max_items=10, description="Flashcard tags")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if not v:
            return []
        # Remove duplicates, strip whitespace, filter empty
        cleaned = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned[:10]  # Limit to 10 tags


class FlashcardCreateRequest(FlashcardBase):
    """Request to create a new flashcard."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "front": {
                    "text": "What is a Python list?",
                    "rich_text": {
                        "format": "html",
                        "content": "<p><strong>What</strong> is a <em>Python list</em>?</p>"
                    }
                },
                "back": {
                    "text": "A Python list is a collection which is ordered and changeable.",
                    "rich_text": {
                        "format": "html",
                        "content": "<p>A Python list is a <strong>collection</strong> which is <em>ordered</em> and <em>changeable</em>.</p>"
                    }
                },
                "hint": "Think about data structures",
                "explanation": "Lists are one of 4 built-in data types in Python used to store collections of data.",
                "difficulty_level": "easy",
                "tags": ["python", "list", "data-structure"]
            }
        }


class FlashcardUpdateRequest(BaseModel):
    """Request to update an existing flashcard."""
    front: Optional[FlashcardContent] = Field(None, description="Front side content")
    back: Optional[FlashcardContent] = Field(None, description="Back side content")
    hint: Optional[str] = Field(None, max_length=500, description="Optional hint")
    explanation: Optional[str] = Field(None, max_length=1000, description="Detailed explanation")
    difficulty_level: Optional[str] = Field(
        None, 
        pattern="^(easy|medium|hard)$",
        description="Flashcard difficulty"
    )
    tags: Optional[List[str]] = Field(None, max_items=10, description="Flashcard tags")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if v is None:
            return None
        # Remove duplicates, strip whitespace, filter empty
        cleaned = list(set(tag.strip().lower() for tag in v if tag.strip()))
        return cleaned[:10]  # Limit to 10 tags

    class Config:
        json_schema_extra = {
            "example": {
                "front": {
                    "text": "What is a Python dictionary?",
                    "rich_text": {
                        "format": "html",
                        "content": "<p><strong>What</strong> is a <em>Python dictionary</em>?</p>"
                    }
                },
                "back": {
                    "text": "A Python dictionary is a collection which is unordered, changeable and indexed.",
                    "rich_text": {
                        "format": "html",
                        "content": "<p>A Python dictionary is a <strong>collection</strong> which is <em>unordered</em>, <em>changeable</em> and <em>indexed</em>.</p>"
                    }
                },
                "difficulty_level": "medium",
                "tags": ["python", "dictionary", "data-structure"]
            }
        }


class FlashcardResponse(BaseModel):
    """Flashcard response model."""
    id: str = Field(alias="_id", description="Flashcard ID")
    deck_id: str = Field(..., description="Parent deck ID")
    front: FlashcardContent = Field(..., description="Front side content")
    back: FlashcardContent = Field(..., description="Back side content")
    hint: Optional[str] = Field(None, description="Optional hint")
    explanation: Optional[str] = Field(None, description="Detailed explanation")
    difficulty_level: str = Field(..., description="Flashcard difficulty")
    tags: List[str] = Field(default_factory=list, description="Flashcard tags")
    
    # Metadata
    order_index: int = Field(0, description="Order within deck")
    created_by: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Study progress (will be implemented later)
    times_reviewed: int = Field(0, description="Number of times reviewed")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True  # Allow both 'id' and '_id'
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "deck_id": "507f1f77bcf86cd799439012",
                "front": {
                    "text": "What is a Python list?",
                    "rich_text": {
                        "format": "html",
                        "content": "<p><strong>What</strong> is a <em>Python list</em>?</p>"
                    }
                },
                "back": {
                    "text": "A Python list is a collection which is ordered and changeable.",
                    "rich_text": {
                        "format": "html", 
                        "content": "<p>A Python list is a <strong>collection</strong> which is <em>ordered</em> and <em>changeable</em>.</p>"
                    }
                },
                "hint": "Think about data structures",
                "explanation": "Lists are one of 4 built-in data types in Python used to store collections of data.",
                "difficulty_level": "easy",
                "tags": ["python", "list", "data-structure"],
                "order_index": 1,
                "created_by": "507f1f77bcf86cd799439013",
                "created_at": "2025-08-08T10:30:00Z",
                "updated_at": "2025-08-08T10:30:00Z",
                "times_reviewed": 5,
                "last_reviewed": "2025-08-08T12:00:00Z"
            }
        }


class FlashcardListResponse(BaseModel):
    """Response for flashcard list."""
    flashcards: List[FlashcardResponse] = Field(..., description="List of flashcards")
    total_count: int = Field(..., description="Total number of flashcards")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
    deck_info: Dict[str, Any] = Field(..., description="Parent deck information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "flashcards": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "deck_id": "507f1f77bcf86cd799439012",
                        "front": {
                            "text": "What is Python?",
                            "rich_text": None
                        },
                        "back": {
                            "text": "Python is a programming language",
                            "rich_text": None
                        },
                        "difficulty_level": "easy",
                        "tags": ["python", "programming"],
                        "order_index": 1,
                        "created_by": "507f1f77bcf86cd799439013",
                        "created_at": "2025-08-08T10:30:00Z",
                        "updated_at": "2025-08-08T10:30:00Z",
                        "times_reviewed": 0,
                        "last_reviewed": None
                    }
                ],
                "total_count": 15,
                "page": 1,
                "limit": 10,
                "total_pages": 2,
                "has_next": True,
                "has_prev": False,
                "deck_info": {
                    "id": "507f1f77bcf86cd799439012",
                    "title": "Python Basics",
                    "description": "Learn Python fundamentals"
                }
            }
        }


class FlashcardBulkCreateRequest(BaseModel):
    """Request to create multiple flashcards."""
    flashcards: List[FlashcardCreateRequest] = Field(..., min_items=1, max_items=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "flashcards": [
                    {
                        "front": {"text": "What is Python?"},
                        "back": {"text": "Python is a programming language"},
                        "difficulty_level": "easy",
                        "tags": ["python", "programming"]
                    },
                    {
                        "front": {"text": "What is a variable?"},
                        "back": {"text": "A variable is a container for storing data"},
                        "difficulty_level": "easy",
                        "tags": ["python", "variables"]
                    }
                ]
            }
        }


class FlashcardBulkCreateResponse(BaseModel):
    """Response for bulk flashcard creation."""
    created_count: int = Field(..., description="Number of flashcards created")
    flashcards: List[FlashcardResponse] = Field(..., description="Created flashcards")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    
    class Config:
        json_schema_extra = {
            "example": {
                "created_count": 2,
                "flashcards": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "deck_id": "507f1f77bcf86cd799439012",
                        "front": {"text": "What is Python?"},
                        "back": {"text": "Python is a programming language"},
                        "difficulty_level": "easy",
                        "tags": ["python", "programming"],
                        "order_index": 1,
                        "created_by": "507f1f77bcf86cd799439013",
                        "created_at": "2025-08-08T10:30:00Z",
                        "updated_at": "2025-08-08T10:30:00Z"
                    }
                ],
                "errors": []
            }
        }
