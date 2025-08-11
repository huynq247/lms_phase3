"""
User profile management endpoints.
"""
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

from app.core.deps import get_current_user
from app.utils.database import get_database
from app.utils.response_standardizer import ResponseStandardizer
from app.models.user import User
from app.models.profile import (
    UserProfileResponse, 
    UserProfileUpdate,
    LearningGoalsUpdate,
    StudyScheduleUpdate, 
    AchievementsResponse,
    LearningGoal,
    StudySession,
    Achievement
)
from app.services.profile_service import ProfileService
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's extended profile information.
    
    Returns:
        UserProfileResponse: Complete user profile with extended features
    """
    try:
        db = await get_database()
        profile_service = ProfileService(db)
        profile = await profile_service.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
            
        # Standardize response format (_id -> id)
        profile_dict = jsonable_encoder(profile)
        return ResponseStandardizer.create_standardized_response(profile_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile information.
    
    Args:
        profile_update: Profile update data
        
    Returns:
        UserProfileResponse: Updated user profile
    """
    try:
        db = await get_database()
        profile_service = ProfileService(db)
        updated_profile = await profile_service.update_user_profile(
            current_user.id, 
            profile_update
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
            
        # Award achievement for first profile update
        achievement_service = AchievementService(db)
        await achievement_service.check_and_award_profile_achievement(current_user.id)
            
        # Standardize response format (_id -> id)
        profile_dict = jsonable_encoder(updated_profile)
        return ResponseStandardizer.create_standardized_response(profile_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )


@router.put("/learning-goals", response_model=UserProfileResponse)
async def update_learning_goals(
    goals_update: LearningGoalsUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update user's learning goals.
    
    Args:
        goals_update: Learning goals update data
        
    Returns:
        UserProfileResponse: Updated user profile
    """
    try:
        db = await get_database()
        profile_service = ProfileService(db)
        updated_profile = await profile_service.update_learning_goals(
            current_user.id,
            goals_update.learning_goals
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
            
        # Award achievement for setting first goal
        achievement_service = AchievementService(db)
        await achievement_service.check_and_award_goal_achievement(current_user.id)
            
        # Standardize response format (_id -> id)
        profile_dict = jsonable_encoder(updated_profile)
        return ResponseStandardizer.create_standardized_response(profile_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update learning goals: {str(e)}"
        )


@router.put("/study-schedule", response_model=UserProfileResponse)
async def update_study_schedule(
    schedule_update: StudyScheduleUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update user's study schedule.
    
    Args:
        schedule_update: Study schedule update data
        
    Returns:
        UserProfileResponse: Updated user profile
    """
    try:
        db = await get_database()
        profile_service = ProfileService(db)
        updated_profile = await profile_service.update_study_schedule(
            current_user.id,
            schedule_update.study_schedule
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
            
        # Award achievement for setting study schedule
        achievement_service = AchievementService(db)
        await achievement_service.check_and_award_schedule_achievement(current_user.id)
            
        # Standardize response format (_id -> id)
        profile_dict = jsonable_encoder(updated_profile)
        return ResponseStandardizer.create_standardized_response(profile_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update study schedule: {str(e)}"
        )


@router.get("/achievements", response_model=AchievementsResponse)
async def get_user_achievements(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's achievements with statistics.
    
    Returns:
        AchievementsResponse: User achievements with category breakdown
    """
    try:
        db = await get_database()
        achievement_service = AchievementService(db)
        achievements_data = await achievement_service.get_user_achievements(current_user.id)
        
        # Standardize response format (_id -> id)
        achievements_dict = jsonable_encoder(achievements_data)
        return ResponseStandardizer.create_standardized_response(achievements_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user achievements: {str(e)}"
        )
