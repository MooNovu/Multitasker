import secrets
from fastapi import HTTPException, UploadFile
import os
import shutil
from app.models.attachment import AttachmentOut

UPLOAD_DIR = "uploads/attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class AttachmentService:
    def __init__(self, db):
        self.db = db

    async def upload_attachment(self, file: UploadFile, user_id: int) -> AttachmentOut:
        cursor = self.db.cursor()

        file_extension = file.filename.split(".")[-1]
        if file_extension not in ['jpg', 'jpeg', 'png']:
            raise HTTPException(
                status_code=400,
                detail="Недопустимый формат файла. Разрешены только JPEG/JPG и PNG."
            )
        file_name = f"{secrets.token_hex(8)}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        cursor.execute(
            "INSERT INTO attachments (file_path, uploaded_by) VALUES (%s, %s) RETURNING id, file_path",
            (f"/uploads/attachments/{file_name}", user_id)
        )
        self.db.commit()
        attachment = cursor.fetchone()

        return AttachmentOut(id=attachment["id"], file_path=attachment["file_path"])