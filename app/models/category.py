from pydantic import BaseModel
from typing import Optional


class CategoryCreate(BaseModel):
    name: str
    color: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    color: str | None

    class Config:
        from_attributes = True

class CategoryUpdate(BaseModel):
    name: str | None = None
    color: str | None = None

class CategoryFilters(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None