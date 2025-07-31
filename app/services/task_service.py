from app.models.task import TaskCreate, TaskOut, TaskUpdate, TaskFilters
from fastapi import HTTPException
from app.models.user import UserOut


class TaskService:
    def __init__(self, db):
        self.db = db

    async def create_task(self, task: TaskCreate, user_id: int) -> TaskOut:
        cursor = self.db.cursor()

        # Проверка существования проекта
        cursor.execute("SELECT id FROM projects WHERE id = %s", (task.project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Проверка исполнителя (должен быть в проекте)
        if task.assignee_id:
            cursor.execute(
                """
                SELECT user_id FROM project_users 
                WHERE project_id = %s AND user_id = %s
                """,
                (task.project_id, task.assignee_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Assignee must be a member of the project")

        # Создание задачи с возвратом данных об авторе и исполнителе
        cursor.execute(
            """
            WITH inserted_task AS (
                INSERT INTO tasks (name, description, due_date, priority, status, author_id, assignee_id, project_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            )
            SELECT 
                it.id, it.name, it.description, it.due_date, it.priority, it.status,
                it.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                it.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin,
                it.project_id
            FROM inserted_task it
            JOIN users ua ON it.author_id = ua.id
            LEFT JOIN users ub ON it.assignee_id = ub.id
            """,
            (
                task.name,
                task.description,
                task.due_date,
                task.priority,
                "в работе",  # Статус по умолчанию
                user_id,  # Текущий пользователь как автор
                task.assignee_id,
                task.project_id
            )
        )
        self.db.commit()
        task_data = cursor.fetchone()

        # Формируем author как UserOut
        author = UserOut(
            id=task_data["author_id"],
            email=task_data["author_email"],
            name=task_data["author_name"],
            avatar_id=task_data["author_avatar_id"]
        )

        # Формируем assignee как UserOut | None
        assignee = None
        if task_data["assignee_id"]:
            assignee = UserOut(
                id=task_data["assignee_id"],
                email=task_data["assignee_email"],
                name=task_data["assignee_name"],
                avatar_id=task_data["assignee_avatar_id"]
            )

        return TaskOut(
            id=task_data["id"],
            name=task_data["name"],
            description=task_data["description"],
            due_date=task_data["due_date"],
            priority=task_data["priority"],
            status=task_data["status"],
            author=author,
            assignee=assignee,
            project_id=task_data["project_id"]
        )

    async def get_user_task(self, filters: TaskFilters, user_id: int) -> list[TaskOut]:
        conditions = ["(t.author_id = %s OR t.assignee_id = %s)"]
        params = [user_id, user_id]

        filters_map = {
            'name': ("t.name LIKE %s", f"%{filters.name}%"),
            'description': ("t.description LIKE %s", f"%{filters.description}%"),
            'priority': ("t.priority = %s", filters.priority),
            'status': ("t.status = %s", filters.status),
            'due_date': ("t.due_date <= %s", filters.due_date),
            'project_id': ("t.project_id = %s", filters.project_id),
            'assignee_id': ("t.assignee_id = %s", filters.assignee_id),
        }

        for field, (condition, value) in filters_map.items():
            if getattr(filters, field) is not None:
                conditions.append(condition)
                params.append(value)

        # Специальные флаги
        if filters.is_completed is not None:
            conditions.append("t.status = %s")
            params.append("выполнена" if filters.is_completed else "в работе")

        if filters.is_overdue is not None:
            conditions.append("t.due_date < CURRENT_DATE AND t.status != %s")
            params.append("выполнена")

        # Собираем финальный запрос с JOIN на users для получения информации об авторе
        query = f"""
                    SELECT 
                        t.id, t.name, t.description, t.due_date, t.priority, t.status,
                        t.author_id, t.assignee_id, t.project_id,
                        ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                        ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
                    FROM tasks t
                    JOIN users ua ON t.author_id = ua.id
                    LEFT JOIN users ub ON t.assignee_id = ub.id
                    WHERE {' AND '.join(conditions)}
                """

        cursor = self.db.cursor()
        cursor.execute(query, tuple(params))
        filtered = cursor.fetchall()

        # Преобразуем результаты в TaskOut с вложенными UserOut для author и assignee
        tasks = []
        for task in filtered:
            author = UserOut(
                id=task["author_id"],
                email=task["author_email"],
                name=task["author_name"],
                avatar_id=task["author_avatar_id"]
            )
            assignee = None
            if task["assignee_id"]:
                assignee = UserOut(
                    id=task["assignee_id"],
                    email=task["assignee_email"],
                    name=task["assignee_name"],
                    avatar_id=task["assignee_avatar_id"]
                )
            tasks.append(TaskOut(
                id=task["id"],
                name=task["name"],
                description=task["description"],
                due_date=task["due_date"],
                priority=task["priority"],
                status=task["status"],
                author=author,
                assignee=assignee,
                project_id=task["project_id"]
            ))
        return tasks

    async def get_task(self, task_id: int, user_id: int) -> TaskOut:
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT 
                t.id, t.name, t.description, t.due_date, t.priority, t.status, 
                t.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                t.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin,
                t.project_id
            FROM tasks t
            JOIN users ua ON t.author_id = ua.id
            LEFT JOIN users ub ON t.assignee_id = ub.id
            WHERE t.id = %s AND (t.author_id = %s OR t.assignee_id = %s)
            """,
            (task_id, user_id, user_id)
        )
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Формируем author как UserOut
        author = UserOut(
            id=task["author_id"],
            email=task["author_email"],
            name=task["author_name"],
            avatar_id=task["author_avatar_id"]
        )

        # Формируем assignee как UserOut | None
        assignee = None
        if task["assignee_id"]:
            assignee = UserOut(
                id=task["assignee_id"],
                email=task["assignee_email"],
                name=task["assignee_name"],
                avatar_id=task["assignee_avatar_id"]
            )

        return TaskOut(
            id=task["id"],
            name=task["name"],
            description=task["description"],
            due_date=task["due_date"],
            priority=task["priority"],
            status=task["status"],
            author=author,
            assignee=assignee,
            project_id=task["project_id"]
        )

    async def update_task(self, task_id: int, task_data: TaskUpdate, user_id: int, is_admin: bool = False) -> TaskOut:
        cursor = self.db.cursor()

        # Проверка существования задачи и получение текущего project_id и author_id
        cursor.execute("SELECT id, project_id, author_id FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        current_project_id = task["project_id"]
        task_author_id = task["author_id"]

        # Проверяем права: администратор, автор задачи или автор проекта
        if not is_admin:
            cursor.execute("SELECT author_id FROM projects WHERE id = %s", (current_project_id,))
            project = cursor.fetchone()
            project_author_id = project["author_id"] if project else None

            if user_id not in (task_author_id, project_author_id):
                raise HTTPException(status_code=403,
                                    detail="Only task author, project author, or admin can update this task")

        # Проверка связанных сущностей
        project_id = task_data.project_id if task_data.project_id is not None else current_project_id
        if task_data.project_id:
            cursor.execute("SELECT id FROM projects WHERE id = %s", (task_data.project_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found")

        if task_data.assignee_id:
            cursor.execute(
                """
                SELECT user_id FROM project_users 
                WHERE project_id = %s AND user_id = %s
                """,
                (project_id, task_data.assignee_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Assignee must be a member of the project")

        # Формирование обновлений
        updates = {k: v for k, v in task_data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
        set_values = list(updates.values())
        values = set_values + [task_id]

        # Выполняем обновление
        cursor.execute(
            f"""
            UPDATE tasks 
            SET {set_clause}
            WHERE id = %s
            RETURNING id
            """,
            values
        )
        updated_task_id = cursor.fetchone()
        if not updated_task_id:
            raise HTTPException(status_code=404, detail="Task not updated")

        self.db.commit()

        # Получаем обновлённые данные с JOIN-ами
        cursor.execute(
            """
            SELECT 
                t.id, t.name, t.description, t.due_date, t.priority, t.status,
                t.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                t.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin,
                t.project_id
            FROM tasks t
            JOIN users ua ON t.author_id = ua.id
            LEFT JOIN users ub ON t.assignee_id = ub.id
            WHERE t.id = %s
            """,
            (task_id,)
        )
        updated_task = cursor.fetchone()

        # Формируем author как UserOut
        author = UserOut(
            id=updated_task["author_id"],
            email=updated_task["author_email"],
            name=updated_task["author_name"],
            avatar_id=updated_task["author_avatar_id"]
        )

        # Формируем assignee как UserOut | None
        assignee = None
        if updated_task["assignee_id"]:
            assignee = UserOut(
                id=updated_task["assignee_id"],
                email=updated_task["assignee_email"],
                name=updated_task["assignee_name"],
                avatar_id=updated_task["assignee_avatar_id"]
            )

        return TaskOut(
            id=updated_task["id"],
            name=updated_task["name"],
            description=updated_task["description"],
            due_date=updated_task["due_date"],
            priority=updated_task["priority"],
            status=updated_task["status"],
            author=author,
            assignee=assignee,
            project_id=updated_task["project_id"]
        )

    async def delete_task(self, task_id: int, user_id: int, is_admin: bool = False):
        cursor = self.db.cursor()

        # Проверка существования задачи и получение author_id и project_id
        cursor.execute("SELECT id, author_id, project_id FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task_author_id = task["author_id"]
        project_id = task["project_id"]

        # Проверяем права: администратор, автор задачи или автор проекта
        if not is_admin:
            cursor.execute("SELECT author_id FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
            project_author_id = project["author_id"] if project else None

            if user_id not in (task_author_id, project_author_id):
                raise HTTPException(status_code=403,
                                    detail="Only task author, project author, or admin can delete this task")

        # Удаляем задачу
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        self.db.commit()