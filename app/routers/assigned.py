from fastapi import APIRouter, Depends
from app.models.assigned import AssignedTaskOut, AssignedTaskFilters
from app.services.assigned_service import get_assigned_tasks
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.get("", response_model=list[AssignedTaskOut])
async def get_assigned(
    filters: AssignedTaskFilters = Depends(),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    return await get_assigned_tasks(current_user["id"], db, filters)