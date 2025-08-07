"""
Deck router with CRUD operations and advanced privacy features.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user
from app.models.deck import (
    DeckCreateRequest, DeckUpdateRequest, DeckResponse, DeckListResponse
)
from app.models.user import User
from app.services.deck_service import DeckService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=DeckListResponse)
async def get_decks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    privacy_level: Optional[str] = Query(None, description="Filter by privacy level"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    owner: Optional[str] = Query(None, description="Filter by owner username"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of decks accessible to current user.
    
    **Privacy Rules:**
    - **Owner**: See all their own decks
    - **Admin**: See all decks 
    - **Teacher/Student**: See public + assigned decks
    
    **Filters:**
    - `privacy_filter`: Filter by privacy level
    - `tags`: Comma-separated tags (e.g., "python,programming")
    - `difficulty`: Filter by difficulty (beginner/intermediate/advanced)
    - `owner`: Filter by owner username
    - `search`: Search in title and description
    """
    try:
        # Parse tags filter
        tags_filter = None
        if tags:
            tags_filter = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # DEBUG: Log parameters
        logger.info(f"Router get_decks called with privacy_level: {privacy_level}")
        
        # Get deck service
        deck_service = DeckService()
        
        # Get accessible decks
        deck_list = await deck_service.get_user_accessible_decks(
            current_user_id=str(current_user.id),
            page=page,
            limit=limit,
            privacy_filter=privacy_level,
            tags_filter=tags_filter,
            difficulty_filter=difficulty,
            owner_filter=owner,
            search_query=search
        )
        
        logger.info(f"User {current_user.username} retrieved {len(deck_list.decks)} decks (page {page})")
        return deck_list
        
    except Exception as e:
        logger.error(f"Error getting decks for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve decks"
        )


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    deck_data: DeckCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new deck.
    
    **Owner Permissions:**
    - **Admin**: Can create any type of deck
    - **Teacher**: Can create all deck types
    - **Student**: Can only create private/public decks
    
    **Privacy Levels:**
    - `private`: Only owner can access
    - `class-assigned`: Assigned to specific classes
    - `course-assigned`: Assigned to specific courses  
    - `lesson-assigned`: Assigned to specific lessons
    - `public`: Everyone can access
    """
    try:
        deck_service = DeckService()
        
        # Create deck
        new_deck = await deck_service.create_deck(
            deck_data=deck_data,
            owner_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.username} created deck: {new_deck.title}")
        return new_deck
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Invalid data for deck creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating deck for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create deck"
        )


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_deck(
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific deck by ID.
    
    **Access Control:**
    - Must have view permission based on privacy level
    - Owner can always access their decks
    - Public decks accessible to everyone
    - Assigned decks accessible to assigned users
    """
    try:
        deck_service = DeckService()
        
        # Get deck
        deck = await deck_service.get_deck_by_id(
            deck_id=deck_id,
            current_user_id=str(current_user.id)
        )
        
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found or access denied"
            )
        
        logger.info(f"User {current_user.username} accessed deck: {deck.title}")
        return deck
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deck {deck_id} for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve deck"
        )


@router.put("/{deck_id}", response_model=DeckResponse)
async def update_deck(
    deck_id: str,
    deck_data: DeckUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update a deck.
    
    **Edit Permissions:**
    - **Owner**: Can edit their own decks
    - **Admin**: Can edit any deck
    - **Others**: Cannot edit
    
    **Privacy Changes:**
    - Can change privacy level if user has permission
    - Assignment changes require appropriate permissions
    """
    try:
        deck_service = DeckService()
        
        # Update deck
        updated_deck = await deck_service.update_deck(
            deck_id=deck_id,
            deck_data=deck_data,
            current_user_id=str(current_user.id)
        )
        
        if not updated_deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        logger.info(f"User {current_user.username} updated deck: {updated_deck.title}")
        return updated_deck
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Invalid data for deck update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating deck {deck_id} for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update deck"
        )


@router.delete("/{deck_id}")
async def delete_deck(
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a deck.
    
    **Delete Permissions:**
    - **Owner**: Can delete their own decks
    - **Admin**: Can delete any deck
    - **Others**: Cannot delete
    
    **Warning:** This action cannot be undone.
    """
    try:
        deck_service = DeckService()
        
        # Delete deck
        success = await deck_service.delete_deck(
            deck_id=deck_id,
            current_user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        logger.info(f"User {current_user.username} deleted deck: {deck_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Deck deleted successfully"}
        )
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting deck {deck_id} for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete deck"
        )
