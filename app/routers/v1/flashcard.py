"""
Flashcard router with multimedia content management.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user
from app.models.user import User
from app.models.flashcard import (
    FlashcardCreateRequest, FlashcardUpdateRequest, FlashcardResponse,
    FlashcardListResponse, FlashcardBulkCreateRequest, FlashcardBulkCreateResponse
)
from app.services.flashcard_service import FlashcardService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("/deck/{deck_id}", response_model=FlashcardListResponse)
async def get_deck_flashcards(
    deck_id: str = Path(..., description="Deck ID to get flashcards for"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (easy/medium/hard)"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    search: Optional[str] = Query(None, description="Search in flashcard content"),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated flashcards for a specific deck.
    
    **Access Control:**
    - Must have view access to the deck
    - Follows same privacy rules as deck access
    
    **Filters:**
    - `difficulty`: Filter by difficulty level
    - `tags`: Comma-separated tags (e.g., "python,programming")
    - `search`: Search in front/back text, hint, explanation
    """
    try:
        # Parse tags filter
        tags_filter = None
        if tags:
            tags_filter = [tag.strip() for tag in tags.split(",") if tag.strip()]

        flashcard_service = FlashcardService()
        
        flashcards = await flashcard_service.get_deck_flashcards(
            deck_id=deck_id,
            current_user_id=str(current_user.id),
            page=page,
            limit=limit,
            difficulty_filter=difficulty,
            tags_filter=tags_filter,
            search_query=search
        )
        
        logger.info(f"User {current_user.username} retrieved {len(flashcards.flashcards)} flashcards from deck {deck_id}")
        return flashcards
        
    except ValueError as e:
        logger.warning(f"Invalid request for deck flashcards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting flashcards for deck {deck_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flashcards"
        )


@router.post("/deck/{deck_id}", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
async def create_flashcard(
    deck_id: str = Path(..., description="Deck ID to create flashcard in"),
    flashcard_data: FlashcardCreateRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new flashcard in a deck.
    
    **Edit Permissions:**
    - **Deck Owner**: Can create flashcards in their deck
    - **Admin**: Can create flashcards in any deck
    - **Others**: Cannot create
    
    **Content Support:**
    - Rich text formatting
    - Image and audio URLs
    - Hints and explanations
    - Difficulty levels and tags
    """
    try:
        flashcard_service = FlashcardService()
        
        new_flashcard = await flashcard_service.create_flashcard(
            deck_id=deck_id,
            flashcard_data=flashcard_data,
            current_user_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.username} created flashcard in deck {deck_id}")
        return new_flashcard
        
    except ValueError as e:
        logger.warning(f"Invalid flashcard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating flashcard in deck {deck_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create flashcard"
        )


@router.get("/{flashcard_id}", response_model=FlashcardResponse)
async def get_flashcard(
    flashcard_id: str = Path(..., description="Flashcard ID to retrieve"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific flashcard by ID.
    
    **Access Control:**
    - Must have view access to the parent deck
    - Follows same privacy rules as deck access
    """
    try:
        flashcard_service = FlashcardService()
        
        flashcard = await flashcard_service.get_flashcard_by_id(
            flashcard_id=flashcard_id,
            current_user_id=str(current_user.id)
        )
        
        if not flashcard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found or access denied"
            )
        
        logger.info(f"User {current_user.username} accessed flashcard {flashcard_id}")
        return flashcard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flashcard"
        )


@router.put("/{flashcard_id}", response_model=FlashcardResponse)
async def update_flashcard(
    flashcard_id: str = Path(..., description="Flashcard ID to update"),
    flashcard_data: FlashcardUpdateRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing flashcard.
    
    **Edit Permissions:**
    - **Deck Owner**: Can edit flashcards in their deck
    - **Admin**: Can edit any flashcard
    - **Others**: Cannot edit
    
    **Update Support:**
    - Partial updates (only provided fields are updated)
    - Rich text content updates
    - Multimedia URL updates
    - Metadata updates
    """
    try:
        flashcard_service = FlashcardService()
        
        updated_flashcard = await flashcard_service.update_flashcard(
            flashcard_id=flashcard_id,
            flashcard_data=flashcard_data,
            current_user_id=str(current_user.id)
        )
        
        if not updated_flashcard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found"
            )
        
        logger.info(f"User {current_user.username} updated flashcard {flashcard_id}")
        return updated_flashcard
        
    except ValueError as e:
        logger.warning(f"Invalid flashcard update data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flashcard"
        )


@router.delete("/{flashcard_id}")
async def delete_flashcard(
    flashcard_id: str = Path(..., description="Flashcard ID to delete"),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a flashcard.
    
    **Delete Permissions:**
    - **Deck Owner**: Can delete flashcards in their deck
    - **Admin**: Can delete any flashcard
    - **Others**: Cannot delete
    
    **Warning:** This action cannot be undone.
    """
    try:
        flashcard_service = FlashcardService()
        
        success = await flashcard_service.delete_flashcard(
            flashcard_id=flashcard_id,
            current_user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found"
            )
        
        logger.info(f"User {current_user.username} deleted flashcard {flashcard_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Flashcard deleted successfully"}
        )
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting flashcard {flashcard_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete flashcard"
        )


@router.post("/deck/{deck_id}/bulk", response_model=FlashcardBulkCreateResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_flashcards(
    deck_id: str = Path(..., description="Deck ID to create flashcards in"),
    bulk_data: FlashcardBulkCreateRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple flashcards at once.
    
    **Edit Permissions:**
    - **Deck Owner**: Can bulk create flashcards in their deck
    - **Admin**: Can bulk create flashcards in any deck
    - **Others**: Cannot create
    
    **Bulk Support:**
    - Up to 50 flashcards per request
    - Partial success handling (some may fail)
    - Error reporting for failed cards
    - Atomic deck counter updates
    """
    try:
        flashcard_service = FlashcardService()
        
        result = await flashcard_service.bulk_create_flashcards(
            deck_id=deck_id,
            bulk_data=bulk_data,
            current_user_id=str(current_user.id)
        )
        
        logger.info(f"User {current_user.username} bulk created {result.created_count} flashcards in deck {deck_id}")
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid bulk flashcard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error bulk creating flashcards in deck {deck_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create flashcards"
        )


# Alternative endpoints with deck prefix for better organization
deck_router = APIRouter(prefix="/decks", tags=["deck-flashcards"])


@deck_router.get("/{deck_id}/flashcards", response_model=FlashcardListResponse)
async def get_deck_flashcards_alt(
    deck_id: str = Path(..., description="Deck ID to get flashcards for"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (easy/medium/hard)"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    search: Optional[str] = Query(None, description="Search in flashcard content"),
    current_user: User = Depends(get_current_user)
):
    """Alternative endpoint: GET /api/v1/decks/{deck_id}/flashcards"""
    # Parse tags filter
    tags_filter = None
    if tags:
        tags_filter = [tag.strip() for tag in tags.split(",") if tag.strip()]

    flashcard_service = FlashcardService()
    
    return await flashcard_service.get_deck_flashcards(
        deck_id=deck_id,
        current_user_id=str(current_user.id),
        page=page,
        limit=limit,
        difficulty_filter=difficulty,
        tags_filter=tags_filter,
        search_query=search
    )


@deck_router.post("/{deck_id}/flashcards", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
async def create_deck_flashcard_alt(
    deck_id: str = Path(..., description="Deck ID to create flashcard in"),
    flashcard_data: FlashcardCreateRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """Alternative endpoint: POST /api/v1/decks/{deck_id}/flashcards"""
    flashcard_service = FlashcardService()
    
    return await flashcard_service.create_flashcard(
        deck_id=deck_id,
        flashcard_data=flashcard_data,
        current_user_id=str(current_user.id)
    )
