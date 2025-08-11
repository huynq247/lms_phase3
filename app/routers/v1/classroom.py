"""Class (Classroom) management router for Phase 5.1 & 5.2"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.encoders import jsonable_encoder

from app.core.deps import get_current_user
from app.utils.response_standardizer import ResponseStandardizer
from app.core.decorators import require_role
from app.models.enums import UserRole
from app.models.user import User
from app.models.classroom import (
    ClassCreateRequest, ClassUpdateRequest, ClassResponse, ClassListResponse,
    EnrollmentRequest, EnrollmentResponse, BulkEnrollmentRequest, 
    BulkEnrollmentResponse, ClassStudentsResponse
)
from app.services.class_service import ClassService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/classes", tags=["class-management"])


@router.get("", response_model=List[ClassListResponse])
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def list_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    teacher_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user)
):
    # Teachers only see their own unless admin or specifying their ID
    if current_user.role == UserRole.TEACHER:
        teacher_id = str(current_user.id)
    service = ClassService()
    classes = await service.list_classes(skip=skip, limit=limit, teacher_id=teacher_id, is_active=is_active)
    
    # Standardize response format (_id -> id)
    classes_dict = jsonable_encoder(classes)
    return ResponseStandardizer.create_standardized_response(classes_dict)


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def create_class(
    class_data: ClassCreateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        service = ClassService()
        created = await service.create_class(class_data, teacher_id=str(current_user.id))
        
        # Standardize response format (_id -> id)
        created_dict = jsonable_encoder(created)
        return ResponseStandardizer.create_standardized_response(created_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{class_id}", response_model=ClassResponse)
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def get_class(class_id: str, current_user: User = Depends(get_current_user)):
    service = ClassService()
    doc = await service.get_class(class_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Class not found")
    # Ownership check for teachers
    if current_user.role == UserRole.TEACHER and doc["teacher_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Standardize response format (_id -> id)
    class_response = ClassResponse(**doc)
    response_dict = jsonable_encoder(class_response)
    return ResponseStandardizer.create_standardized_response(response_dict)


@router.put("/{class_id}", response_model=ClassResponse)
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def update_class(
    class_id: str,
    class_data: ClassUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        service = ClassService()
        updated = await service.update_class(class_id, class_data, current_user_id=str(current_user.id))
        if not updated:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Standardize response format (_id -> id)
        updated_dict = jsonable_encoder(updated)
        return ResponseStandardizer.create_standardized_response(updated_dict)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{class_id}")
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def delete_class(class_id: str, current_user: User = Depends(get_current_user)):
    try:
        service = ClassService()
        success = await service.delete_class(class_id, current_user_id=str(current_user.id))
        if not success:
            raise HTTPException(status_code=404, detail="Class not found")
        
        response_data = {"message": "Class deleted"}
        response_dict = jsonable_encoder(response_data)
        return ResponseStandardizer.create_standardized_response(response_dict)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Phase 5.2 - Enrollment Management Endpoints

@router.post("/{class_id}/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def enroll_student(
    class_id: str,
    enrollment_data: EnrollmentRequest,
    current_user: User = Depends(get_current_user)
):
    """Enroll a student in a class."""
    try:
        logger.info(f"User {current_user.id} attempting to enroll student {enrollment_data.user_id} in class {class_id}")
        service = ClassService()
        enrollment = await service.enroll_student(
            class_id=class_id,
            user_id=enrollment_data.user_id,
            current_user_id=str(current_user.id)
        )
        logger.info(f"Successfully enrolled student {enrollment_data.user_id} in class {class_id}")
        
        # Standardize response format (_id -> id)
        enrollment_dict = jsonable_encoder(enrollment)
        return ResponseStandardizer.create_standardized_response(enrollment_dict)
    except ValueError as e:
        logger.warning(f"Enrollment validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Enrollment permission error: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during enrollment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{class_id}/enroll/{user_id}")
@require_role([UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN])
async def unenroll_student(
    class_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unenroll a student from a class."""
    try:
        logger.info(f"User {current_user.id} attempting to unenroll student {user_id} from class {class_id}")
        service = ClassService()
        success = await service.unenroll_student(
            class_id=class_id,
            user_id=user_id,
            current_user_id=str(current_user.id)
        )
        if not success:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        
        logger.info(f"Successfully unenrolled student {user_id} from class {class_id}")
        
        response_data = {"message": "Student unenrolled successfully"}
        response_dict = jsonable_encoder(response_data)
        return ResponseStandardizer.create_standardized_response(response_dict)
    except ValueError as e:
        logger.warning(f"Unenrollment validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Unenrollment permission error: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during unenrollment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{class_id}/students", response_model=ClassStudentsResponse)
@require_role([UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN])
async def get_class_students(
    class_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get list of students enrolled in a class."""
    try:
        service = ClassService()
        students = await service.get_class_students(
            class_id=class_id,
            current_user_id=str(current_user.id)
        )
        
        # Standardize response format (_id -> id)
        students_dict = jsonable_encoder(students)
        return ResponseStandardizer.create_standardized_response(students_dict)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{class_id}/bulk-enroll", response_model=BulkEnrollmentResponse, status_code=status.HTTP_201_CREATED)
@require_role([UserRole.TEACHER, UserRole.ADMIN])
async def bulk_enroll_students(
    class_id: str,
    csv_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Bulk enroll students via CSV file upload."""
    try:
        logger.info(f"User {current_user.id} attempting bulk enrollment for class {class_id}")
        
        # Validate file type and size
        if not csv_file.filename or not csv_file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV with .csv extension")
        
        # Check file size (limit to 1MB)
        content = await csv_file.read()
        if len(content) > 1024 * 1024:  # 1MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 1MB")
        
        try:
            csv_data = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
        
        service = ClassService()
        result = await service.bulk_enroll_students(
            class_id=class_id,
            csv_data=csv_data,
            current_user_id=str(current_user.id)
        )
        
        logger.info(f"Bulk enrollment completed: {result.successful_enrollments}/{result.total_processed} successful")
        
        # Standardize response format (_id -> id)
        result_dict = jsonable_encoder(result)
        return ResponseStandardizer.create_standardized_response(result_dict)
        
    except ValueError as e:
        logger.warning(f"Bulk enrollment validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Bulk enrollment permission error: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during bulk enrollment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during bulk enrollment")
