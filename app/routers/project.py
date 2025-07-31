from fastapi import APIRouter, Depends
from app.models.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectFilters, ProjectAddUser, \
    ProjectDetailOut, ProjectTasksOut
from app.services.project_service import ProjectService
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("", response_model=ProjectOut, status_code=201)
async def create_new_project(
    project: ProjectCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.create_project(project, current_user["id"])

@router.post("/add_user_to_project", response_model=dict)
async def add_user_to_existing_project(
    project_add_user: ProjectAddUser,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.add_user_to_project(project_add_user, current_user["id"])

@router.delete("/remove_user_from_project", response_model=dict)
async def remove_user_from_existing_project(
    project_add_user: ProjectAddUser,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.remove_user_from_project(project_add_user, current_user["id"], is_admin=current_user["is_admin"])

@router.get("", response_model=list[ProjectOut])
async def get_projects(
    filters: ProjectFilters = Depends(),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.get_user_projects(filters, current_user["id"])

@router.get("/{project_id}", response_model=ProjectDetailOut, status_code=200)
async def get_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.get_project(project_id, current_user["id"])

@router.get("/tasks/{project_id}", response_model=ProjectTasksOut, status_code=200)
async def get_project_tasks_subtasks(
    project_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.get_project_tasks_and_subtasks(project_id, current_user["id"])

@router.put("/{project_id}", response_model=ProjectOut)
async def update_existing_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.update_project(project_id, project_data, current_user["id"], is_admin=current_user["is_admin"])

@router.delete("/{project_id}", response_model=None, status_code=204)
async def delete_existing_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    project_service = ProjectService(db)
    return await project_service.delete_project(project_id, current_user["id"], is_admin=current_user["is_admin"])