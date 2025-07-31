from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    code: str
    new_password: str

#Редактировать профиль
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

#Возврат при входе в профиль
class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None
    avatar_id: int | None

    class Config:
        from_attributes = True