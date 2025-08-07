"""
Category models for deck categorization system.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class CategoryBase(BaseModel):
    """Base category model."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    icon: Optional[str] = Field(None, description="Category icon (emoji or icon name)")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Category color in hex format")
    is_predefined: bool = Field(False, description="Whether this is a predefined system category")


class CategoryCreateRequest(CategoryBase):
    """Request model for creating a category."""
    pass


class CategoryUpdateRequest(BaseModel):
    """Request model for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryResponse(CategoryBase):
    """Response model for category."""
    id: str = Field(..., description="Category ID")
    deck_count: int = Field(0, description="Number of decks in this category")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_by_username: Optional[str] = Field(None, description="Creator username")

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """Response model for category list."""
    categories: List[CategoryResponse]
    total_count: int
    predefined_count: int
    custom_count: int


class PredefinedCategory(BaseModel):
    """Model for predefined category data."""
    name: str
    description: str
    icon: str
    color: str


# Predefined categories data
PREDEFINED_CATEGORIES = [
    PredefinedCategory(
        name="Language Learning",
        description="Decks for learning foreign languages",
        icon="🗣️",
        color="#FF6B6B"
    ),
    PredefinedCategory(
        name="Mathematics",
        description="Mathematical concepts and formulas",
        icon="🔢",
        color="#4ECDC4"
    ),
    PredefinedCategory(
        name="Science",
        description="Physics, Chemistry, Biology and other sciences",
        icon="🔬",
        color="#45B7D1"
    ),
    PredefinedCategory(
        name="History",
        description="Historical events, dates and figures",
        icon="📚",
        color="#96CEB4"
    ),
    PredefinedCategory(
        name="Literature",
        description="Literature, poetry and language arts",
        icon="📖",
        color="#FFEAA7"
    ),
    PredefinedCategory(
        name="Computer Science",
        description="Programming, algorithms and technology",
        icon="💻",
        color="#6C5CE7"
    ),
    PredefinedCategory(
        name="Medical",
        description="Medical terminology and health sciences",
        icon="⚕️",
        color="#FD79A8"
    ),
    PredefinedCategory(
        name="Business",
        description="Business, economics and finance",
        icon="💼",
        color="#FDCB6E"
    ),
    PredefinedCategory(
        name="Geography",
        description="Countries, capitals and geographical features",
        icon="🗺️",
        color="#55A3FF"
    ),
    PredefinedCategory(
        name="General Knowledge",
        description="Mixed topics and general trivia",
        icon="🧠",
        color="#81ECEC"
    )
]
