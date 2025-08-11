"""
Category router for deck categorization endpoints.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.core.deps import get_current_user
from app.utils.response_standardizer import ResponseStandardizer
from app.models.category import (
    CategoryCreateRequest, CategoryUpdateRequest, 
    CategoryResponse, CategoryListResponse
)
from app.models.user import User
from app.services.category_service import CategoryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
async def get_categories():
    """
    Get all categories with deck counts.
    
    **Returns:**
    - All predefined and custom categories
    - Deck count for each category
    - Summary statistics
    """
    try:
        category_service = CategoryService()
        categories = await category_service.get_categories()
        
        logger.info(f"Retrieved {categories.total_count} categories")
        
        # Standardize response format (_id -> id)
        categories_dict = jsonable_encoder(categories)
        return ResponseStandardizer.create_standardized_response(categories_dict)
        
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new category (admin only).
    
    **Admin only endpoint** for creating custom categories.
    
    **Requirements:**
    - User must have admin role
    - Category name must be unique
    """
    try:
        category_service = CategoryService()
        category = await category_service.create_category(
            category_data=category_data,
            creator_id=str(current_user.id)
        )
        
        logger.info(f"Admin {current_user.username} created category: {category.name}")
        
        # Standardize response format (_id -> id)
        category_dict = jsonable_encoder(category)
        return ResponseStandardizer.create_standardized_response(category_dict)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_data: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update category (admin only).
    
    **Admin only endpoint** for updating categories.
    
    **Restrictions:**
    - Cannot change name of predefined categories
    - Category name must be unique if changing
    """
    try:
        category_service = CategoryService()
        category = await category_service.update_category(
            category_id=category_id,
            category_data=category_data,
            updater_id=str(current_user.id)
        )
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        logger.info(f"Admin {current_user.username} updated category: {category.name}")
        
        # Standardize response format (_id -> id)
        category_dict = jsonable_encoder(category)
        return ResponseStandardizer.create_standardized_response(category_dict)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category"
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete category (admin only).
    
    **Admin only endpoint** for deleting custom categories.
    
    **Restrictions:**
    - Cannot delete predefined categories
    - Cannot delete categories with existing decks
    """
    try:
        category_service = CategoryService()
        deleted = await category_service.delete_category(
            category_id=category_id,
            deleter_id=str(current_user.id)
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        logger.info(f"Admin {current_user.username} deleted category: {category_id}")
        
        response_data = {"message": "Category deleted successfully"}
        response_dict = jsonable_encoder(response_data)
        standardized_response = ResponseStandardizer.create_standardized_response(response_dict)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=standardized_response
        )
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_predefined_categories(
    current_user: User = Depends(get_current_user)
):
    """
    Seed predefined categories (admin only).
    
    **Admin only endpoint** for seeding system predefined categories.
    """
    try:
        category_service = CategoryService()
        seeded_count = await category_service.seed_predefined_categories()
        
        logger.info(f"Admin {current_user.username} seeded {seeded_count} predefined categories")
        
        response_data = {
            "message": f"Seeded {seeded_count} predefined categories",
            "seeded_count": seeded_count
        }
        response_dict = jsonable_encoder(response_data)
        standardized_response = ResponseStandardizer.create_standardized_response(response_dict)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=standardized_response
        )
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error seeding predefined categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to seed predefined categories"
        )
