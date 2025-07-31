from fastapi import APIRouter, Depends
from app.models.subtask import SubtaskCreate, SubtaskUpdate, SubtaskOut
from app.services.subtask_service import SubtaskService
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("", response_model=SubtaskOut, status_code=201)
async def create_new_subtask(
    subtask: SubtaskCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    subtask_service = SubtaskService(db)
    return await subtask_service.create_subtask(subtask, current_user["id"])

@router.get("", response_model=list[SubtaskOut])
async def get_subtasks(
    task_id: int | None = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    subtask_service = SubtaskService(db)
    return await subtask_service.get_user_subtasks(current_user["id"], task_id)

@router.get("/{subtask_id}", response_model=SubtaskOut)
async def get_subtask(
    subtask_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    subtask_service = SubtaskService(db)
    return await subtask_service.get_subtask(subtask_id, current_user["id"])

@router.put("/{subtask_id}", response_model=SubtaskOut)
async def update_existing_subtask(
    subtask_id: int,
    subtask_data: SubtaskUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    subtask_service = SubtaskService(db)
    return await subtask_service.update_subtask(subtask_id, subtask_data, current_user["id"], is_admin=current_user["is_admin"])

@router.delete("/{subtask_id}", response_model=None, status_code=204)
async def delete_existing_subtask(
    subtask_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    subtask_service = SubtaskService(db)
    await subtask_service.delete_subtask(subtask_id, current_user["id"], is_admin=current_user["is_admin"])