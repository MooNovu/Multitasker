from pydantic import BaseModel
from datetime import date
from typing import Literal, Optional, List

class CalendarFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[Literal["в работе", "выполнена", "просрочена"]] = None

class CalendarEntry(BaseModel):
    id: int
    name: str
    due_date: date
    priority: str
    status: str
    project_id: int | None
    task_id: int | None  # None для задач, ID родительской задачи для подзадач
    type: Literal["task", "subtask"]

class CalendarOut(BaseModel):
    date: date
    tasks: List[CalendarEntry]