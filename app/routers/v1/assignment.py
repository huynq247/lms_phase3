"""
Assignment API router for deck assignments and privacy management.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.core.deps import get_current_user
from app.models.user import User
from app.models.assignment import (
    DeckAssignmentCreate, DeckAssignmentResponse, AssignmentListResponse,
    DeckPrivacyUpdateRequest, AssignmentType
)
from app.services.assignment_service import AssignmentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.put("/decks/{deck_id}/privacy", response_model=dict)
async def update_deck_privacy(
    deck_id: str = Path(..., description="Deck ID to update privacy"),
    privacy_data: DeckPrivacyUpdateRequest = ...,
    current_user: User = Depends(get_current_user)
):
    """
    Update deck privacy level and assignments.
    
    **Permission Requirements:**
    - **Admin**: Can update any deck privacy
    - **Teacher**: Can update any deck privacy  
    - **Deck Owner**: Can update their own deck privacy
    - **Others**: Permission denied
    
    **Privacy Levels:**
    - `private`: Owner only
    - `class-assigned`: Assigned to specific classes
    - `course-assigned`: Assigned to specific courses
    - `lesson-assigned`: Assigned to specific lessons
    - `public`: Everyone can access
    """
    try:
        assignment_service = AssignmentService()
        
        success = await assignment_service.update_deck_privacy(
            deck_id=deck_id,
            privacy_data=privacy_data,
            current_user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found or update failed"
            )
        
        logger.info(f"User {current_user.username} updated privacy for deck {deck_id}")
        return {"message": "Deck privacy updated successfully"}
        
    except ValueError as e:
        logger.warning(f"Privacy update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating deck privacy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update deck privacy"
        )


@router.post("/decks/{deck_id}/assign/class/{class_id}", response_model=DeckAssignmentResponse)
async def assign_deck_to_class(
    deck_id: str = Path(..., description="Deck ID to assign"),
    class_id: str = Path(..., description="Class ID to assign deck to"),
    current_user: User = Depends(get_current_user)
):
    """
    Assign deck to a specific class.
    
    **Permission Requirements:**
    - **Admin**: Can assign any deck
    - **Teacher**: Can assign any deck
    - **Deck Owner**: Can assign their own deck
    """
    try:
        assignment_service = AssignmentService()
        
        assignment_data = DeckAssignmentCreate(
            deck_id=deck_id,
            assignment_type=AssignmentType.CLASS,
            target_id=class_id,
            assigned_by=str(current_user.id)
        )
        
        assignment = await assignment_service.create_assignment(
            assignment_data=assignment_data,
            current_user_id=str(current_user.id)
        )
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create assignment"
            )
        
        logger.info(f"User {current_user.username} assigned deck {deck_id} to class {class_id}")
        return assignment
        
    except ValueError as e:
        logger.warning(f"Class assignment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning deck to class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign deck to class"
        )


@router.post("/decks/{deck_id}/assign/course/{course_id}", response_model=DeckAssignmentResponse)
async def assign_deck_to_course(
    deck_id: str = Path(..., description="Deck ID to assign"),
    course_id: str = Path(..., description="Course ID to assign deck to"),
    current_user: User = Depends(get_current_user)
):
    """
    Assign deck to a specific course.
    
    **Permission Requirements:**
    - **Admin**: Can assign any deck
    - **Teacher**: Can assign any deck
    - **Deck Owner**: Can assign their own deck
    """
    try:
        assignment_service = AssignmentService()
        
        assignment_data = DeckAssignmentCreate(
            deck_id=deck_id,
            assignment_type=AssignmentType.COURSE,
            target_id=course_id,
            assigned_by=str(current_user.id)
        )
        
        assignment = await assignment_service.create_assignment(
            assignment_data=assignment_data,
            current_user_id=str(current_user.id)
        )
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create assignment"
            )
        
        logger.info(f"User {current_user.username} assigned deck {deck_id} to course {course_id}")
        return assignment
        
    except ValueError as e:
        logger.warning(f"Course assignment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning deck to course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign deck to course"
        )


@router.post("/decks/{deck_id}/assign/lesson/{lesson_id}", response_model=DeckAssignmentResponse)
async def assign_deck_to_lesson(
    deck_id: str = Path(..., description="Deck ID to assign"),
    lesson_id: str = Path(..., description="Lesson ID to assign deck to"),
    current_user: User = Depends(get_current_user)
):
    """
    Assign deck to a specific lesson.
    
    **Permission Requirements:**
    - **Admin**: Can assign any deck
    - **Teacher**: Can assign any deck
    - **Deck Owner**: Can assign their own deck
    """
    try:
        assignment_service = AssignmentService()
        
        assignment_data = DeckAssignmentCreate(
            deck_id=deck_id,
            assignment_type=AssignmentType.LESSON,
            target_id=lesson_id,
            assigned_by=str(current_user.id)
        )
        
        assignment = await assignment_service.create_assignment(
            assignment_data=assignment_data,
            current_user_id=str(current_user.id)
        )
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create assignment"
            )
        
        logger.info(f"User {current_user.username} assigned deck {deck_id} to lesson {lesson_id}")
        return assignment
        
    except ValueError as e:
        logger.warning(f"Lesson assignment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning deck to lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign deck to lesson"
        )


@router.delete("/{assignment_id}", response_model=dict)
async def remove_assignment(
    assignment_id: str = Path(..., description="Assignment ID to remove"),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a deck assignment.
    
    **Permission Requirements:**
    - **Admin**: Can remove any assignment
    - **Teacher**: Can remove any assignment
    - **Assignment Creator**: Can remove their own assignment
    - **Deck Owner**: Can remove assignments for their deck
    """
    try:
        assignment_service = AssignmentService()
        
        success = await assignment_service.remove_assignment(
            assignment_id=assignment_id,
            current_user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        logger.info(f"User {current_user.username} removed assignment {assignment_id}")
        return {"message": "Assignment removed successfully"}
        
    except ValueError as e:
        logger.warning(f"Assignment removal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove assignment"
        )


@router.get("/decks/{deck_id}", response_model=AssignmentListResponse)
async def get_deck_assignments(
    deck_id: str = Path(..., description="Deck ID to get assignments for"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
):
    """
    Get all assignments for a specific deck.
    
    **Permission Requirements:**
    - **Admin**: Can view assignments for any deck
    - **Teacher**: Can view assignments for any deck
    - **Deck Owner**: Can view assignments for their own deck
    """
    try:
        assignment_service = AssignmentService()
        
        assignments = await assignment_service.get_deck_assignments(
            deck_id=deck_id,
            current_user_id=str(current_user.id),
            page=page,
            limit=limit
        )
        
        logger.info(f"User {current_user.username} retrieved assignments for deck {deck_id}")
        return assignments
        
    except ValueError as e:
        logger.warning(f"Get deck assignments error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting deck assignments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deck assignments"
        )
