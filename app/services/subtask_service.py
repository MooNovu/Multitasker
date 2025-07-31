from app.models.subtask import SubtaskCreate, SubtaskUpdate, SubtaskOut
from fastapi import HTTPException
from app.models.user import UserOut


class SubtaskService:
    def __init__(self, db):
        self.db = db

    async def create_subtask(self, subtask: SubtaskCreate, user_id: int) -> SubtaskOut:
        cursor = self.db.cursor()

        # Проверка существования родительской задачи и владения
        cursor.execute("SELECT id, project_id FROM tasks WHERE id = %s AND author_id = %s", (subtask.task_id, user_id))
        parent_task = cursor.fetchone()
        if not parent_task:
            raise HTTPException(status_code=404, detail="Task not found or not owned by user")
        project_id = parent_task["project_id"]

        # Проверка исполнителя
        if subtask.assignee_id:
            cursor.execute(
                """
                SELECT user_id FROM project_users 
                WHERE project_id = %s AND user_id = %s
                """,
                (project_id, subtask.assignee_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Assignee must be a member of the project")

        # Вставка подзадачи и получение данных с JOIN-ами
        cursor.execute(
            """
            WITH inserted_subtask AS (
                INSERT INTO subtasks (task_id, name, description, due_date, priority, status, author_id, assignee_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            )
            SELECT 
                ist.id, ist.task_id, ist.name, ist.description, ist.due_date, ist.priority, ist.status,
                ist.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                ist.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
            FROM inserted_subtask ist
            JOIN users ua ON ist.author_id = ua.id
            LEFT JOIN users ub ON ist.assignee_id = ub.id
            """,
            (subtask.task_id, subtask.name, subtask.description, subtask.due_date, subtask.priority,
             subtask.status, user_id, subtask.assignee_id)
        )
        self.db.commit()
        subtask_data = cursor.fetchone()

        # Формируем author и assignee
        author = UserOut(
            id=subtask_data["author_id"],
            email=subtask_data["author_email"],
            name=subtask_data["author_name"],
            avatar_id=subtask_data["author_avatar_id"]
        )
        assignee = None
        if subtask_data["assignee_id"]:
            assignee = UserOut(
                id=subtask_data["assignee_id"],
                email=subtask_data["assignee_email"],
                name=subtask_data["assignee_name"],
                avatar_id=subtask_data["assignee_avatar_id"]
            )

        return SubtaskOut(
            id=subtask_data["id"],
            task_id=subtask_data["task_id"],
            name=subtask_data["name"],
            description=subtask_data["description"],
            due_date=subtask_data["due_date"],
            priority=subtask_data["priority"],
            status=subtask_data["status"],
            author=author,
            assignee=assignee
        )


    async def get_user_subtasks(self, user_id: int, task_id: int | None = None) -> list[SubtaskOut]:
        cursor = self.db.cursor()

        if task_id:
            # Фильтр по конкретной задаче
            query = """
                    SELECT 
                        s.id, s.task_id, s.name, s.description, s.due_date, s.priority, s.status, 
                        s.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                        s.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
                    FROM subtasks s
                    JOIN users ua ON s.author_id = ua.id
                    LEFT JOIN users ub ON s.assignee_id = ub.id
                    WHERE s.task_id = %s AND (s.author_id = %s OR s.assignee_id = %s)
                """
            params = (task_id, user_id, user_id)
        else:
            # Все подзадачи пользователя
            query = """
                    SELECT 
                        s.id, s.task_id, s.name, s.description, s.due_date, s.priority, s.status, 
                        s.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                        s.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
                    FROM subtasks s
                    JOIN users ua ON s.author_id = ua.id
                    LEFT JOIN users ub ON s.assignee_id = ub.id
                    WHERE s.author_id = %s OR s.assignee_id = %s
                """
            params = (user_id, user_id)

        cursor.execute(query, params)
        subtasks = cursor.fetchall()

        # Преобразуем результаты
        result = []
        for sub in subtasks:
            author = UserOut(
                id=sub["author_id"],
                email=sub["author_email"],
                name=sub["author_name"],
                avatar_id=sub["author_avatar_id"]
            )
            assignee = None
            if sub["assignee_id"]:
                assignee = UserOut(
                    id=sub["assignee_id"],
                    email=sub["assignee_email"],
                    name=sub["assignee_name"],
                    avatar_id=sub["assignee_avatar_id"]
                )
            result.append(SubtaskOut(
                id=sub["id"],
                task_id=sub["task_id"],
                name=sub["name"],
                description=sub["description"],
                due_date=sub["due_date"],
                priority=sub["priority"],
                status=sub["status"],
                author=author,
                assignee=assignee
            ))
        return result

    async def get_subtask(self, subtask_id: int, user_id: int) -> SubtaskOut:
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT 
                s.id, s.task_id, s.name, s.description, s.due_date, s.priority, s.status, 
                s.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                s.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
            FROM subtasks s
            JOIN users ua ON s.author_id = ua.id
            LEFT JOIN users ub ON s.assignee_id = ub.id
            WHERE s.id = %s AND (s.author_id = %s OR s.assignee_id = %s)
            """,
            (subtask_id, user_id, user_id)
        )
        subtask = cursor.fetchone()
        if not subtask:
            raise HTTPException(status_code=404, detail="Subtask not found or not owned by user")

        # Формируем author и assignee
        author = UserOut(
            id=subtask["author_id"],
            email=subtask["author_email"],
            name=subtask["author_name"],
            avatar_id=subtask["author_avatar_id"]
        )
        assignee = None
        if subtask["assignee_id"]:
            assignee = UserOut(
                id=subtask["assignee_id"],
                email=subtask["assignee_email"],
                name=subtask["assignee_name"],
                avatar_id=subtask["assignee_avatar_id"]
            )

        return SubtaskOut(
            id=subtask["id"],
            task_id=subtask["task_id"],
            name=subtask["name"],
            description=subtask["description"],
            due_date=subtask["due_date"],
            priority=subtask["priority"],
            status=subtask["status"],
            author=author,
            assignee=assignee
        )

    async def update_subtask(self, subtask_id: int, subtask_data: SubtaskUpdate, user_id: int,
                             is_admin: bool = False) -> SubtaskOut:
        cursor = self.db.cursor()

        # Проверка существования подзадачи
        cursor.execute("SELECT id, task_id, author_id FROM subtasks WHERE id = %s", (subtask_id,))
        subtask = cursor.fetchone()
        if not subtask:
            raise HTTPException(status_code=404, detail="Subtask not found")
        task_id = subtask["task_id"]
        subtask_author_id = subtask["author_id"]

        # Получаем project_id и task_author_id из родительской задачи
        cursor.execute("SELECT project_id, author_id FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Parent task not found")
        project_id = task["project_id"]
        task_author_id = task["author_id"]

        # Проверяем права: администратор, автор подзадачи, автор задачи или автор проекта
        if not is_admin:
            cursor.execute("SELECT author_id FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
            project_author_id = project["author_id"] if project else None

            if user_id not in (subtask_author_id, task_author_id, project_author_id):
                raise HTTPException(status_code=403,
                                    detail="Only subtask author, task author, project author, or admin can update this subtask")

        # Проверка исполнителя
        if subtask_data.assignee_id:
            cursor.execute(
                "SELECT user_id FROM project_users WHERE project_id = %s AND user_id = %s",
                (project_id, subtask_data.assignee_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Assignee must be a member of the project")

        # Формирование обновлений
        updates = {k: v for k, v in subtask_data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
        set_values = list(updates.values())
        values = set_values + [subtask_id]

        # Выполняем обновление
        cursor.execute(
            f"""
            UPDATE subtasks 
            SET {set_clause}
            WHERE id = %s
            RETURNING id
            """,
            values
        )
        updated_subtask_id = cursor.fetchone()
        if not updated_subtask_id:
            raise HTTPException(status_code=404, detail="Subtask not updated")

        self.db.commit()

        # Получаем обновлённые данные
        cursor.execute(
            """
            SELECT 
                s.id, s.task_id, s.name, s.description, s.due_date, s.priority, s.status,
                s.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                s.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
            FROM subtasks s
            JOIN users ua ON s.author_id = ua.id
            LEFT JOIN users ub ON s.assignee_id = ub.id
            WHERE s.id = %s
            """,
            (subtask_id,)
        )
        updated_subtask = cursor.fetchone()

        author = UserOut(
            id=updated_subtask["author_id"],
            email=updated_subtask["author_email"],
            name=updated_subtask["author_name"],
            avatar_id=updated_subtask["author_avatar_id"]
        )
        assignee = None
        if updated_subtask["assignee_id"]:
            assignee = UserOut(
                id=updated_subtask["assignee_id"],
                email=updated_subtask["assignee_email"],
                name=updated_subtask["assignee_name"],
                avatar_id=updated_subtask["assignee_avatar_id"]
            )

        return SubtaskOut(
            id=updated_subtask["id"],
            task_id=updated_subtask["task_id"],
            name=updated_subtask["name"],
            description=updated_subtask["description"],
            due_date=updated_subtask["due_date"],
            priority=updated_subtask["priority"],
            status=updated_subtask["status"],
            author=author,
            assignee=assignee
        )

    async def delete_subtask(self, subtask_id: int, user_id: int, is_admin: bool = False):
        cursor = self.db.cursor()

        # Проверка существования подзадачи
        cursor.execute("SELECT id, task_id, author_id FROM subtasks WHERE id = %s", (subtask_id,))
        subtask = cursor.fetchone()
        if not subtask:
            raise HTTPException(status_code=404, detail="Subtask not found")
        task_id = subtask["task_id"]
        subtask_author_id = subtask["author_id"]

        # Получаем project_id и task_author_id из родительской задачи
        cursor.execute("SELECT project_id, author_id FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Parent task not found")
        project_id = task["project_id"]
        task_author_id = task["author_id"]

        # Проверяем права: администратор, автор подзадачи, автор задачи или автор проекта
        if not is_admin:
            cursor.execute("SELECT author_id FROM projects WHERE id = %s", (project_id,))
            project = cursor.fetchone()
            project_author_id = project["author_id"] if project else None

            if user_id not in (subtask_author_id, task_author_id, project_author_id):
                raise HTTPException(status_code=403,
                                    detail="Only subtask author, task author, project author, or admin can delete this subtask")

        # Удаляем подзадачу
        cursor.execute("DELETE FROM subtasks WHERE id = %s", (subtask_id,))
        self.db.commit()