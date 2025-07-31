from fastapi import HTTPException
from app.models.user import UserCreate, UserLogin, PasswordResetRequest, PasswordReset
from app.services.email_service import EmailService
from app.config import settings
from jose import jwt
from datetime import datetime, timedelta
import secrets

class AuthService:
    def __init__(self, db):
        self.db = db

    async def register_user(self, user: UserCreate) -> None:
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&*+-.<=>?@^_"
        if not (8 <= len(user.password) <= 16 and all(c in allowed_chars for c in user.password)):
            raise HTTPException(status_code=400, detail="Password must be 8-16 characters with allowed symbols")

        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (user.email, user.password))
        self.db.commit()


    async def login_user(self, user: UserLogin) -> str:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (user.email, user.password))
        db_user = cursor.fetchone()
        if not db_user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        token = jwt.encode(
            {"sub": str(db_user["id"]), "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return token


    async def request_password_reset(self, request: PasswordResetRequest) -> dict:
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (request.email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        reset_code = secrets.token_hex(3)
        cursor.execute(
            "INSERT INTO password_reset_codes (user_id, code) VALUES (%s, %s)",
            (user["id"], reset_code)
        )
        self.db.commit()
        email_service = EmailService()
        return await email_service.send_email(
            to_email=f"{request.email}",
            subject="Восстановление пароля",
            body=f"Reset code for {request.email}: {reset_code}")


    async def reset_password(self, request: PasswordReset) -> None:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT user_id FROM password_reset_codes WHERE code = %s AND expires_at > CURRENT_TIMESTAMP",
            (request.code,)
        )
        reset_data = cursor.fetchone()
        if not reset_data:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code")

        user_id = reset_data["user_id"]
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&*+-.<=>?@^_"
        if not (8 <= len(request.new_password) <= 16 and all(c in allowed_chars for c in request.new_password)):
            raise HTTPException(status_code=400, detail="Password must be 8-16 characters with allowed symbols")

        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (request.new_password, user_id)
        )
        cursor.execute("DELETE FROM password_reset_codes WHERE code = %s", (request.code,))
        self.db.commit()