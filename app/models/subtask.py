from pydantic import BaseModel
from datetime import date
from typing import Literal, Optional
from app.models.user import UserOut

class SubtaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: date
    priority: Literal["низкий", "средний", "высокий"]
    status: Literal["в работе", "выполнена", "просрочена"] = "в работе"
    task_id: int
    assignee_id: Optional[int] = None

class SubtaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[Literal["низкий", "средний", "высокий"]] = None
    status: Optional[Literal["в работе", "выполнена", "просрочена"]] = None
    assignee_id: Optional[int] = None

class SubtaskOut(BaseModel):
    id: int
    task_id: int
    name: str
    description: Optional[str]
    due_date: date
    priority: str
    status: str
    author: UserOut
    assignee: Optional[UserOut]

    class Config:
        from_attributes = True