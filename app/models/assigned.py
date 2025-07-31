from pydantic import BaseModel
from typing import Literal, Optional
from datetime import date
from app.models.user import UserOut


# Модель для фильтров (если захочешь)
class AssignedTaskFilters(BaseModel):
    name: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[Literal["низкий", "средний", "высокий"]] = None
    status: Optional[Literal["в работе", "выполнена", "просрочена"]] = None
    project_id: Optional[int] = None
    is_overdue: Optional[bool] = None
    task_id: Optional[int] = None
    task_type: Optional[Literal["task", "subtask"]] = None

# Общая модель для ответа (задачи и подзадачи)
class AssignedTaskOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    due_date: date
    priority: str
    status: str
    author: UserOut
    assignee: UserOut
    project_id: int | None  # Для подзадач может быть None, если брать из задачи
    task_id: int | None  # None для задач, ID родительской задачи для подзадач
    type: Literal["task", "subtask"]  # Указывает, что это: задача или подзадача

    class Config:
        from_attributes = True