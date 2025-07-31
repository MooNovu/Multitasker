from pydantic import BaseModel
from datetime import date
from typing import Literal, Optional, List
from app.models.user import UserOut


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    due_date: date
    priority: Literal["низкий", "средний", "высокий"]
    project_id: int
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    due_date: date | None = None
    priority: Literal["низкий", "средний", "высокий"] | None = None
    status: Literal["в работе", "выполнена", "просрочена"] | None = None
    assignee_id: int | None = None
    project_id: int | None = None


class TaskOut(BaseModel):
    id: int
    name: str
    description: str | None
    due_date: date
    priority: Literal["низкий", "средний", "высокий"]
    status: str
    author: UserOut
    assignee: UserOut | None
    project_id: int

    class Config:
        from_attributes = True

class TaskFilters(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[Literal["низкий", "средний", "высокий"]] = None
    status: Optional[Literal["в работе", "выполнена", "просрочена"]] = None
    author_id: Optional[int] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    is_completed: Optional[bool] = None
    is_overdue: Optional[bool] = None
