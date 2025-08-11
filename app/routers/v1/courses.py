"""Course API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from datetime import datetime

from app.models.course import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
    CourseFilterRequest,
    CoursesListResponse,
    CourseStatsResponse
)
from app.models.user import User
from app.services.course_service import CourseService
from app.core.deps import get_current_user, get_database
from app.utils.response_standardizer import ResponseStandardizer
from app.models.enums import DifficultyLevel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


def get_course_service(db=Depends(get_database)) -> CourseService:
    """Get course service instance."""
    return CourseService(db)


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreateRequest,
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Create a new course."""
    try:
        # Only teachers and admins can create courses
        if current_user.role not in ["teacher", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers and admins can create courses"
            )
        
        course = await course_service.create_course(course_data, current_user)
        logger.info(f"Course created by user {current_user.username}")
        
        # Standardize response format (_id -> id)
        course_dict = jsonable_encoder(course)
        return ResponseStandardizer.create_standardized_response(course_dict)
        
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )


@router.get("/", response_model=CoursesListResponse)
async def get_courses(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty_level: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty level"),
    creator_id: Optional[str] = Query(None, description="Filter by creator ID"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Get courses with filtering and pagination."""
    try:
        filters = CourseFilterRequest(
            category=category,
            difficulty_level=difficulty_level,
            creator_id=creator_id,
            is_public=is_public,
            tags=tags,
            search=search
        )
        
        courses = await course_service.get_courses(filters, current_user, skip, limit)
        logger.info(f"Retrieved {len(courses.courses)} courses for user {current_user.username}")
        
        # Standardize response format (_id -> id)
        courses_dict = jsonable_encoder(courses)
        return ResponseStandardizer.create_standardized_response(courses_dict)
        
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch courses"
        )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Get a specific course by ID."""
    try:
        course = await course_service.get_course_by_id(course_id, current_user)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or access denied"
            )
        
        logger.info(f"Course {course_id} retrieved by user {current_user.username}")
        
        # Standardize response format (_id -> id)
        course_dict = jsonable_encoder(course)
        return ResponseStandardizer.create_standardized_response(course_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course"
        )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdateRequest,
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Update a course."""
    try:
        course = await course_service.update_course(course_id, course_data, current_user)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        logger.info(f"Course {course_id} updated by user {current_user.username}")
        
        # Standardize response format (_id -> id)
        course_dict = jsonable_encoder(course)
        return ResponseStandardizer.create_standardized_response(course_dict)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Delete a course (soft delete)."""
    try:
        success = await course_service.delete_course(course_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        logger.info(f"Course {course_id} deleted by user {current_user.username}")
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )


@router.get("/{course_id}/stats", response_model=CourseStatsResponse)
async def get_course_stats(
    course_id: str,
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Get course statistics."""
    try:
        stats = await course_service.get_course_stats(course_id, current_user)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or access denied"
            )
        
        logger.info(f"Course stats for {course_id} retrieved by user {current_user.username}")
        
        # Standardize response format (_id -> id)
        stats_dict = jsonable_encoder(stats)
        return ResponseStandardizer.create_standardized_response(stats_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course stats {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course stats"
        )
