from pydantic import BaseModel

class AttachmentOut(BaseModel):
    id: int
    file_path: str

    class Config:
        from_attributes = True