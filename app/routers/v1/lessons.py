"""Lesson API endpoints for individual lesson operations."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from app.models.lesson import (
    LessonUpdate,
    LessonResponse,
    LessonPrerequisiteCheck
)
from app.models.user import User
from app.services.lesson_service import LessonService
from app.services.course_service import CourseService
from app.core.deps import get_current_user, get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lessons", tags=["lessons"])


def get_lesson_service(db=Depends(get_database)) -> LessonService:
    """Get lesson service instance."""
    return LessonService(db)


def get_course_service(db=Depends(get_database)) -> CourseService:
    """Get course service instance."""
    return CourseService(db)


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Get a specific lesson by ID."""
    try:
        lesson = await lesson_service.get_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        
        # Get course to check permissions
        course = await course_service.get_course_by_id(lesson.course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check
        if current_user.role == "student":
            # Students can only see published lessons in courses they have access to
            if not lesson.is_published:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lesson not published")
            # TODO: Check if student is enrolled in course
        elif current_user.role == "teacher":
            # Teachers can see lessons in their courses or public courses
            if course.created_by != current_user.id and course.privacy_level != "public" and current_user.role != "admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        # Admins can see all lessons
        
        logger.info(f"Retrieved lesson {lesson_id} for user {current_user.id}")
        return lesson
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson {lesson_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lesson"
        )


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: str,
    lesson_data: LessonUpdate,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Update a specific lesson."""
    try:
        # Get existing lesson
        existing_lesson = await lesson_service.get_lesson(lesson_id)
        if not existing_lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        
        # Get course to check permissions
        course = await course_service.get_course_by_id(existing_lesson.course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: Only course creator or admin can update lessons
        if current_user.role not in ["admin", "teacher"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        if current_user.role == "teacher" and course.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only update lessons in your own courses")
        
        updated_lesson = await lesson_service.update_lesson(
            lesson_id=lesson_id,
            lesson_data=lesson_data,
            updated_by=current_user.id
        )
        
        if not updated_lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        
        logger.info(f"Updated lesson {lesson_id} by user {current_user.id}")
        return updated_lesson
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating lesson {lesson_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lesson"
        )


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Delete a specific lesson (soft delete)."""
    try:
        # Get existing lesson
        existing_lesson = await lesson_service.get_lesson(lesson_id)
        if not existing_lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        
        # Get course to check permissions
        course = await course_service.get_course_by_id(existing_lesson.course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: Only course creator or admin can delete lessons
        if current_user.role not in ["admin", "teacher"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        if current_user.role == "teacher" and course.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only delete lessons in your own courses")
        
        success = await lesson_service.delete_lesson(lesson_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        
        logger.info(f"Deleted lesson {lesson_id} by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lesson {lesson_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lesson"
        )


@router.get("/{lesson_id}/prerequisites", response_model=LessonPrerequisiteCheck)
async def check_lesson_prerequisites(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service)
):
    """Check if user has met lesson prerequisites."""
    try:
        prerequisite_check = await lesson_service.check_lesson_prerequisites(
            lesson_id=lesson_id,
            user_id=current_user.id
        )
        
        logger.info(f"Checked prerequisites for lesson {lesson_id} for user {current_user.id}")
        return prerequisite_check
        
    except Exception as e:
        logger.error(f"Error checking lesson prerequisites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check lesson prerequisites"
        )
