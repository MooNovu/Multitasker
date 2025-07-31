from app.models.assigned import AssignedTaskOut, AssignedTaskFilters
from app.models.user import UserOut

async def get_assigned_tasks(user_id: int, db, filters: AssignedTaskFilters | None = None) -> list[AssignedTaskOut]:
    cursor = db.cursor()

    task_conditions = ["t.assignee_id = %s"]
    subtask_conditions = ["s.assignee_id = %s"]
    task_params = [user_id]
    subtask_params = [user_id]

    # Фильтры
    if filters:
        filters_map = {
            "name": ("name LIKE %s", f"%{filters.name}%"),
            "due_date": ("due_date <= %s", filters.due_date),
            "priority": ("priority = %s", filters.priority),
            "status": ("status = %s", filters.status),
            "project_id": ("project_id = %s", filters.project_id),
        }

        # Обрабатываем общие фильтры
        for field, (condition, value) in filters_map.items():
            if getattr(filters, field) is not None:
                task_conditions.append(f"t.{condition}")
                subtask_conditions.append(
                    f"s.{condition}" if field != "project_id" else "s.task_id IN (SELECT id FROM tasks WHERE project_id = %s)"
                )
                task_params.append(value)
                subtask_params.append(value)

        # Обрабатываем фильтр task_id отдельно для задач и подзадач
        if filters.task_id is not None:
            task_conditions.append("t.id = %s")  # Для задач фильтруем по id
            subtask_conditions.append("s.task_id = %s")  # Для подзадач фильтруем по task_id
            task_params.append(filters.task_id)
            subtask_params.append(filters.task_id)

    # Запрос для задач
    task_query = f"""
        SELECT 
            t.id, t.name, t.description, t.due_date, t.priority, t.status,
            t.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
            t.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin,
            t.project_id, NULL AS task_id, 'task' AS type
        FROM tasks t
        JOIN users ua ON t.author_id = ua.id
        JOIN users ub ON t.assignee_id = ub.id
        WHERE {' AND '.join(task_conditions)}
    """

    # Запрос для подзадач
    subtask_query = f"""
        SELECT 
            s.id, s.name, s.description, s.due_date, s.priority, s.status,
            s.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
            s.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin,
            (SELECT project_id FROM tasks WHERE tasks.id = s.task_id) AS project_id,
            s.task_id, 'subtask' AS type
        FROM subtasks s
        JOIN users ua ON s.author_id = ua.id
        JOIN users ub ON s.assignee_id = ub.id
        WHERE {' AND '.join(subtask_conditions)}
    """

    # Учитываем фильтр по типу
    if filters and filters.task_type:
        if filters.task_type == "task":
            final_query = task_query
            params = task_params
        elif filters.task_type == "subtask":
            final_query = subtask_query
            params = subtask_params
    else:
        # Если фильтр по типу не указан, объединяем оба запроса
        final_query = f"{task_query} UNION ALL {subtask_query}"
        params = task_params + subtask_params  # Комбинируем параметры для UNION

    cursor.execute(final_query, tuple(params))
    assigned = cursor.fetchall()

    # Преобразуем результаты в AssignedTaskOut
    result = []
    for item in assigned:
        author = UserOut(
            id=item["author_id"],
            email=item["author_email"],
            name=item["author_name"],
            avatar_id=item["author_avatar_id"]
        )
        assignee = UserOut(
            id=item["assignee_id"],
            email=item["assignee_email"],
            name=item["assignee_name"],
            avatar_id=item["assignee_avatar_id"]
        )
        result.append(AssignedTaskOut(
            id=item["id"],
            name=item["name"],
            description=item["description"],
            due_date=item["due_date"],
            priority=item["priority"],
            status=item["status"],
            author=author,
            assignee=assignee,
            project_id=item["project_id"],
            task_id=item["task_id"],
            type=item["type"]
        ))
    return result