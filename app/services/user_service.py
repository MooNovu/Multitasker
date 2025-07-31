import os
import shutil
from app.models.user import UserUpdate, UserOut
from fastapi import HTTPException
from fastapi.responses import FileResponse

class UserService:
    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int) -> UserOut:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT id, email, name, avatar_id, is_admin FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut(**user)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserOut:
        cursor = self.db.cursor()

        # Проверка уникальности email, если он обновляется
        if user_data.email:
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (user_data.email, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")

        # Формируем запрос только с обновляемыми полями
        updates = {}
        if user_data.email is not None:
            updates["email"] = user_data.email
        if user_data.name is not None:
            updates["name"] = user_data.name
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Генерируем SQL-запрос динамически
        set_placeholder = ", ".join(f"{key} = %s" for key in updates.keys())
        values = list(updates.values()) + [user_id]

        cursor.execute(
            f"UPDATE users SET {set_placeholder} WHERE id = %s RETURNING id, email, name, avatar_id",
            values
        )
        self.db.commit()
        updated_user = cursor.fetchone()

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserOut(**updated_user)

    async def set_avatar(self, user_id: int, attachment_id: int) -> UserOut:
        cursor = self.db.cursor()

        # Проверяем, существует ли attachment
        cursor.execute("SELECT id FROM attachments WHERE id = %s", (attachment_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Attachment not found")

        # Обновляем avatar_id
        cursor.execute(
            "UPDATE users SET avatar_id = %s WHERE id = %s RETURNING id, email, name, avatar_id, is_admin",
            (attachment_id, user_id)
        )
        self.db.commit()
        updated_user = cursor.fetchone()

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserOut(**updated_user)