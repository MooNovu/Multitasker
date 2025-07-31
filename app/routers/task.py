from fastapi import APIRouter, Depends, Query, Body
from app.models.task import TaskCreate, TaskOut, TaskUpdate, TaskFilters
from app.services.task_service import TaskService
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("", response_model=TaskOut, status_code=201)
async def create_new_task(
        task: TaskCreate,
        current_user=Depends(get_current_user),
        db=Depends(get_db)
):
    task_service = TaskService(db)
    created_task = task_service.create_task(task, current_user["id"])
    return await created_task

@router.get("", response_model=list[TaskOut])
async def get_tasks(
        filters: TaskFilters = Depends(),
        current_user=Depends(get_current_user),
        db=Depends(get_db)
):
    task_service = TaskService(db)
    return await task_service.get_user_task(filters, current_user["id"])

@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    task_service = TaskService(db)
    return await task_service.get_task(task_id, current_user["id"])

@router.put("/{task_id}", response_model=TaskOut)
async def update_existing_task(
        task_id: int,
        task_data: TaskUpdate,
        current_user=Depends(get_current_user),
        db=Depends(get_db)
):
    task_service = TaskService(db)
    return await task_service.update_task(task_id, task_data, current_user["id"], is_admin=current_user["is_admin"])

@router.delete("/{task_id}", response_model=None, status_code=204)
async def delete_existing_task(
        task_id: int,
        current_user = Depends(get_current_user),
        db = Depends(get_db)
):
    task_service = TaskService(db)
    return await task_service.delete_task(task_id, current_user["id"], is_admin=current_user["is_admin"])