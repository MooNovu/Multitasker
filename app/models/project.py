from pydantic import BaseModel
from typing import Optional, List

from app.models.task import TaskOut
from app.models.user import UserOut
from datetime import date

class ProjectCreate(BaseModel):
    name: str
    category_id: int | None = None

class ProjectAddUser(BaseModel):
    project_id: int
    user_id: int

class ProjectUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None

class ProjectOut(BaseModel):
    id: int
    name: str
    author: UserOut
    category_id: int | None

    class Config:
        from_attributes = True

class ProjectDetailOut(BaseModel):
    id: int
    name: str
    author: UserOut
    category_id: int | None
    users: List[UserOut]

    class Config:
        from_attributes = True

class ProjectFilters(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None


#Для гигаGET запороса

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

class TaskWithSubtasksOut(TaskOut):
    subtasks: List[SubtaskOut]

class ProjectTasksOut(BaseModel):
    id: int
    name: str
    author: UserOut
    tasks: List[TaskWithSubtasksOut]