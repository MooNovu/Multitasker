from fastapi import APIRouter, Depends, Query, Body
from app.models.user import UserCreate, UserLogin, PasswordResetRequest, PasswordReset
from app.services.auth_service import AuthService
from app.database import get_db

router = APIRouter()


@router.post("/register", response_model=dict, status_code=201)
async def register(user: UserCreate,db=Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.register_user(user)
    return {"message": "User registered successfully"}

@router.post("/login", response_model=dict, status_code=200)
async def login(user: UserLogin, db=Depends(get_db)):
    auth_service = AuthService(db)
    token = await auth_service.login_user(user)
    return {"message": "Login successful", "access_token": token}

@router.post("/forgot-password", response_model=dict, status_code=202)
async def forgot_password(request: PasswordResetRequest, db=Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.request_password_reset(request)


@router.post("/reset-password", response_model=dict, status_code=200)
async def reset_pwd(request: PasswordReset, db=Depends(get_db)):
    auth_service = AuthService(db)
    await auth_service.reset_password(request)
    return {"message": "Password reset successfully"}