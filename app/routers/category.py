from fastapi import APIRouter, Depends
from app.models.category import CategoryCreate, CategoryUpdate, CategoryOut, CategoryFilters
from app.services.category_service import CategoryService
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("", response_model=CategoryOut, status_code=201)
async def create_new_category(category: CategoryCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    category_service = CategoryService(db)
    return await category_service.create_category(category, current_user["id"])

@router.get("", response_model=list[CategoryOut])
async def get_categories(
    filters: CategoryFilters = Depends(),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    category_service = CategoryService(db)
    return await category_service.get_user_categories(filters, current_user["id"])

@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    category_service = CategoryService(db)
    return await category_service.get_category(category_id, current_user["id"])

@router.put("/{category_id}", response_model=CategoryOut)
async def update_existing_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    category_service = CategoryService(db)
    return await category_service.update_category(category_id, category_data, current_user["id"], is_admin=current_user["is_admin"])

@router.delete("/{category_id}", response_model=None, status_code=204)
async def delete_existing_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    category_service = CategoryService(db)
    return await category_service.delete_category(category_id, current_user["id"], is_admin=current_user["is_admin"])