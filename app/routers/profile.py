from fastapi import APIRouter, Depends, UploadFile, File
from app.models.user import UserOut, UserUpdate
from app.dependencies import get_current_user
from app.services.user_service import UserService
from app.database import get_db

router = APIRouter()

#Профиль, возвращает (email, name, avatar)
@router.get("", response_model=UserOut)
async def get_profile(current_user=Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", status_code=200)
async def get_user(user_id: int, db=Depends(get_db)):
    profile_service = UserService(db)
    return await profile_service.get_user(user_id)

@router.put("", response_model=UserOut)
async def update_profile(user_data: UserUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.update_user(current_user["id"], user_data)

@router.put("/set-avatar", response_model=UserOut, status_code=200)
async def set_avatar(
    attachment_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    profile_service = UserService(db)
    return await profile_service.set_avatar(current_user["id"], attachment_id)