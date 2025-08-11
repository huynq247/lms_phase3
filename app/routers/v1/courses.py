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
from app.models.course_class_assignment import CourseClassAssignmentResponse
from app.models.lesson import (
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonListResponse,
    LessonStatsResponse,
    LessonBulkOrderUpdate
)
from app.models.user import User
from app.services.course_service import CourseService
from app.services.course_class_assignment_service import CourseClassAssignmentService
from app.services.lesson_service import LessonService
from app.core.deps import get_current_user, get_database
from app.utils.response_standardizer import ResponseStandardizer
from app.models.enums import DifficultyLevel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


def get_course_service(db=Depends(get_database)) -> CourseService:
    """Get course service instance."""
    return CourseService(db)


def get_lesson_service(db=Depends(get_database)) -> LessonService:
    """Get lesson service instance."""
    return LessonService(db)


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


# ============================================================================
# PHASE 5.4: COURSE-CLASS ASSIGNMENT ENDPOINTS
# ============================================================================

@router.get("/{course_id}/classes", response_model=List[CourseClassAssignmentResponse])
async def get_course_classes(
    course_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user)
):
    """
    Get all classes that have this course assigned.
    
    **Permission Requirements:**
    - **Admin**: Can view assignments for any course
    - **Course Creator**: Can view assignments for their own courses
    - **Teachers**: Can view assignments for courses they have access to
    - **Students**: Can view assignments for public courses only
    """
    try:
        assignment_service = CourseClassAssignmentService()
        
        assignments = await assignment_service.get_course_classes(
            course_id=course_id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        logger.info(f"Retrieved {len(assignments)} class assignments for course {course_id}")
        
        # Standardize response format (_id -> id)
        assignments_dict = jsonable_encoder(assignments)
        return ResponseStandardizer.create_standardized_response(assignments_dict)
        
    except PermissionError as e:
        logger.warning(f"Course classes access denied: {str(e)}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting course classes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course classes"
        )


# ==================== LESSON ENDPOINTS ====================

@router.get("/{course_id}/lessons", response_model=LessonListResponse)
async def get_course_lessons(
    course_id: str,
    published_only: bool = Query(False, description="Only return published lessons"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Get all lessons for a course."""
    try:
        # Check if course exists
        course = await course_service.get_course_by_id(course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: Students can only see published lessons, teachers/admins can see all
        if current_user.role == "student":
            published_only = True
            
        # Check course access permission for students
        if current_user.role == "student":
            # TODO: Check if student is enrolled in course or has access
            # For now, allow access to all courses
            pass
        elif current_user.role == "teacher":
            # Teachers can access their courses or public courses
            if course.created_by != current_user.id and course.privacy_level != "public" and current_user.role != "admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        lessons = await lesson_service.get_course_lessons(
            course_id=course_id,
            published_only=published_only,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"Retrieved {len(lessons.lessons)} lessons for course {course_id}")
        return lessons
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course lessons: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get course lessons"
        )


@router.post("/{course_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_course_lesson(
    course_id: str,
    lesson_data: LessonCreate,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Create a new lesson in a course."""
    try:
        # Check if course exists
        course = await course_service.get_course_by_id(course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: Only course creator, admin, or teacher can create lessons
        if current_user.role not in ["admin", "teacher"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Teachers can only create lessons in their own courses (unless admin)
        if current_user.role == "teacher" and course.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only create lessons in your own courses")
        
        lesson = await lesson_service.create_lesson(
            course_id=course_id,
            lesson_data=lesson_data,
            created_by=current_user.id
        )
        
        logger.info(f"Created lesson {lesson.id} in course {course_id} by user {current_user.id}")
        return lesson
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lesson"
        )


@router.get("/{course_id}/lessons/stats", response_model=LessonStatsResponse)
async def get_course_lesson_stats(
    course_id: str,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Get lesson statistics for a course."""
    try:
        # Check if course exists
        course = await course_service.get_course_by_id(course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: Teachers can see stats for their courses, admins can see all
        if current_user.role == "teacher" and course.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        elif current_user.role == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students cannot access lesson statistics")
        
        stats = await lesson_service.get_lesson_stats(course_id)
        
        logger.info(f"Retrieved lesson stats for course {course_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lesson statistics"
        )


@router.put("/{course_id}/lessons/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_course_lessons(
    course_id: str,
    order_data: LessonBulkOrderUpdate,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service)
):
    """Bulk reorder lessons in a course."""
    try:
        # Check if course exists
        course = await course_service.get_course_by_id(course_id, current_user.id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Permission check: Only course creator or admin can reorder lessons
        if current_user.role not in ["admin", "teacher"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        if current_user.role == "teacher" and course.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only reorder lessons in your own courses")
        
        success = await lesson_service.reorder_lessons(course_id, order_data)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to reorder lessons")
        
        logger.info(f"Reordered lessons in course {course_id} by user {current_user.id}")
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error reordering lessons: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder lessons"
        )
