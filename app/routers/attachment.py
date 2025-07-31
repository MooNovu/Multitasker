import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.models.attachment import AttachmentOut
from app.services.attachment_service import AttachmentService
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    attachment_service = AttachmentService(db)
    return await attachment_service.upload_attachment(file, current_user["id"])

@router.get("/{attachment_id}", status_code=200)
async def download_attachment(attachment_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT file_path FROM attachments WHERE id = %s", (attachment_id,))
    attachment = cursor.fetchone()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = attachment["file_path"].lstrip("/")
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="multipart/form-data"
    )