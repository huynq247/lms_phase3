"""
Study Session API Router for Phase 6.1
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user
from app.models.user import User
from app.models.study import (
    StudySessionStartRequest, StudySessionResponse, FlashcardAnswerRequest,
    SessionAnswerResponse, SessionBreakRequest, SessionBreakResponse,
    SessionCompletionResponse, StudyMode
)
from app.services.study_session_service import study_session_service

router = APIRouter(prefix="/study/sessions", tags=["Study Sessions"])


@router.get("/health")
async def health_check():
    """Health check for study session service - No authentication required"""
    return {
        "service": "Study Sessions",
        "status": "healthy", 
        "version": "6.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Session Management",
            "Multiple Study Modes", 
            "Break Reminders",
            "Progress Tracking"
        ]
    }


@router.post("/start", response_model=StudySessionResponse)
async def start_study_session(
    session_request: StudySessionStartRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start a new study session
    
    **Permissions:** Any authenticated user
    **Features:**
    - Multiple study modes (Review, Practice, Cram, Test, Learn)
    - Goal-based sessions (time/card targets)  
    - Break reminder configuration
    - Card selection based on study mode
    """
    try:
        response = await study_session_service.start_session(
            user_id=str(current_user.id),
            session_request=session_request
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start study session: {str(e)}"
        )


@router.get("/{session_id}", response_model=StudySessionResponse)
async def get_study_session(
    session_id: str = Path(..., description="Study session ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Get current study session state
    
    **Permissions:** Session owner only
    **Features:**
    - Current session progress
    - Next flashcard to study
    - Break reminder status
    - Completion percentage
    """
    try:
        response = await study_session_service.get_session(
            session_id=session_id,
            user_id=str(current_user.id)
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get study session: {str(e)}"
        )


@router.put("/{session_id}/answer", response_model=SessionAnswerResponse)
async def submit_flashcard_answer(
    answer_request: FlashcardAnswerRequest,
    session_id: str = Path(..., description="Study session ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Submit answer for current flashcard
    
    **Permissions:** Session owner only
    **Features:**
    - Quality rating (SM-2 scale 0-5)
    - Response time tracking
    - Automatic progress to next card
    - Break reminder checks
    - Performance feedback
    """
    try:
        response = await study_session_service.submit_answer(
            session_id=session_id,
            user_id=str(current_user.id),
            answer_request=answer_request
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.post("/{session_id}/break", response_model=SessionBreakResponse)
async def take_session_break(
    break_request: SessionBreakRequest,
    session_id: str = Path(..., description="Study session ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Take a break during study session
    
    **Permissions:** Session owner only
    **Features:**
    - Configurable break duration
    - Break count tracking
    - Resume time calculation
    - Session pause handling
    """
    try:
        response = await study_session_service.take_break(
            session_id=session_id,
            user_id=str(current_user.id),
            break_request=break_request
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process break: {str(e)}"
        )


@router.post("/{session_id}/complete", response_model=SessionCompletionResponse)
async def complete_study_session(
    session_id: str = Path(..., description="Study session ID"),
    completion_type: str = Query("manual", description="Completion type: goal/manual"),
    current_user: User = Depends(get_current_user)
):
    """
    Complete study session
    
    **Permissions:** Session owner only
    **Features:**
    - Session summary generation
    - Performance metrics calculation
    - Achievement checking
    - Next session recommendations
    """
    try:
        response = await study_session_service.complete_session(
            session_id=session_id,
            user_id=str(current_user.id),
            completion_type=completion_type
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete session: {str(e)}"
        )


@router.get("/active", response_model=List[StudySessionResponse])
async def get_active_sessions(
    current_user: User = Depends(get_current_user)
):
    """
    Get all active sessions for current user
    
    **Permissions:** Own sessions only
    **Features:**
    - List all active/paused sessions
    - Session filtering and sorting
    - Quick session access
    """
    try:
        sessions = await study_session_service.get_active_sessions(
            user_id=str(current_user.id)
        )
        
        return sessions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active sessions: {str(e)}"
        )


@router.delete("/{session_id}")
async def abandon_session(
    session_id: str = Path(..., description="Study session ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Abandon study session without completing
    
    **Permissions:** Session owner only
    **Features:**
    - Mark session as abandoned
    - Clean up session data
    - Preserve partial progress
    """
    try:
        success = await study_session_service.abandon_session(
            session_id=session_id,
            user_id=str(current_user.id)
        )
        
        return {"message": "Session abandoned successfully", "success": success}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to abandon session: {str(e)}"
        )
