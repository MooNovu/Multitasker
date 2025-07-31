from app.models.project import *
from fastapi import HTTPException

from app.models.user import UserOut


class ProjectService:
    def __init__(self, db):
        self.db = db

    async def create_project(self, project: ProjectCreate, user_id: int) -> ProjectOut:
        cursor = self.db.cursor()
        if project.category_id:
            cursor.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s", (project.category_id, user_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Category not found or not owned by user")

        # Вставка проекта и получение данных об авторе
        cursor.execute(
            """
            WITH inserted_project AS (
                INSERT INTO projects (name, author_id, category_id) 
                VALUES (%s, %s, %s) 
                RETURNING id, name, author_id, category_id
            )
            SELECT 
                ip.id, ip.name, ip.author_id, 
                u.email AS author_email, u.name AS author_name, u.avatar_id AS author_avatar_id, u.is_admin AS author_is_admin,
                ip.category_id
            FROM inserted_project ip
            JOIN users u ON ip.author_id = u.id
            """,
            (project.name, user_id, project.category_id)
        )
        project_data = cursor.fetchone()

        # Добавляем автора в project_users
        cursor.execute(
            "INSERT INTO project_users (project_id, user_id) VALUES (%s, %s)",
            (project_data["id"], user_id)
        )
        self.db.commit()

        # Формируем author как UserOut
        author = UserOut(
            id=project_data["author_id"],
            email=project_data["author_email"],
            name=project_data["author_name"],
            avatar_id=project_data["author_avatar_id"]
        )

        return ProjectOut(
            id=project_data["id"],
            name=project_data["name"],
            author=author,
            category_id=project_data["category_id"]
        )

    async def add_user_to_project(self, project_add_user: ProjectAddUser, current_user_id: int) -> dict:
        cursor = self.db.cursor()
        cursor.execute("SELECT author_id FROM projects WHERE id = %s", (project_add_user.project_id,))
        project = cursor.fetchone()
        if not project or project["author_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Only author can add users")

        cursor.execute("SELECT id FROM users WHERE id = %s", (project_add_user.user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute(
            "INSERT INTO project_users (project_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (project_add_user.project_id, project_add_user.user_id)
        )
        self.db.commit()
        return {"message": "User added to project"}

    async def remove_user_from_project(self, project_remove_user: ProjectAddUser, current_user_id: int,
                                       is_admin: bool = False) -> dict:
        cursor = self.db.cursor()

        # Проверка существования проекта и прав доступа
        cursor.execute("SELECT author_id FROM projects WHERE id = %s", (project_remove_user.project_id,))
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        project_author_id = project["author_id"]

        if not is_admin and project_author_id != current_user_id:
            raise HTTPException(status_code=403, detail="Only project author or admin can remove users")

        # Проверка существования пользователя
        cursor.execute("SELECT id FROM users WHERE id = %s", (project_remove_user.user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # Проверка, что пользователь действительно в проекте
        cursor.execute(
            "SELECT user_id FROM project_users WHERE project_id = %s AND user_id = %s",
            (project_remove_user.project_id, project_remove_user.user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User is not a member of the project")

        # Удаляем пользователя из проекта
        cursor.execute(
            "DELETE FROM project_users WHERE project_id = %s AND user_id = %s",
            (project_remove_user.project_id, project_remove_user.user_id)
        )
        cursor.execute(
            "UPDATE tasks SET assignee_id = NULL WHERE project_id = %s AND assignee_id = %s",
            (project_remove_user.project_id, project_remove_user.user_id)
        )
        cursor.execute(
            "UPDATE subtasks SET assignee_id = NULL WHERE task_id IN (SELECT id FROM tasks WHERE project_id = %s) AND assignee_id = %s",
            (project_remove_user.project_id, project_remove_user.user_id)
        )
        self.db.commit()

        return {"message": "User removed from project"}

    async def get_project(self, project_id: int, user_id: int) -> ProjectDetailOut:
        cursor = self.db.cursor()

        # Получаем данные проекта с автором как UserOut
        cursor.execute(
            """
            SELECT 
                p.id, p.name, 
                p.author_id, u.email AS author_email, u.name AS author_name, u.avatar_id AS author_avatar_id, u.is_admin AS author_is_admin,
                p.category_id
            FROM projects p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN project_users pu ON p.id = pu.project_id
            WHERE p.id = %s AND (pu.user_id = %s OR p.author_id = %s)
            """,
            (project_id, user_id, user_id)
        )
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        # Получаем список пользователей проекта
        cursor.execute(
            """
            SELECT u.id, u.email, u.name, u.avatar_id, u.is_admin
            FROM users u
            JOIN project_users pu ON u.id = pu.user_id
            WHERE pu.project_id = %s
            """,
            (project_id,)
        )
        users = cursor.fetchall()

        # Формируем author как UserOut
        author = UserOut(
            id=project["author_id"],
            email=project["author_email"],
            name=project["author_name"],
            avatar_id=project["author_avatar_id"]
        )

        user_list = [UserOut(**user) for user in users]
        return ProjectDetailOut(
            id=project["id"],
            name=project["name"],
            author=author,
            category_id=project["category_id"],
            users=user_list
        )

    async def get_user_projects(self, filters: ProjectFilters, user_id: int) -> list[ProjectOut]:
        cursor = self.db.cursor()

        conditions = ["p.author_id = %s"]
        params = [user_id]

        filters_map = {
            "name": ("p.name LIKE %s", f"%{filters.name}%"),
            "category_id": ("p.category_id = %s", filters.category_id),
        }

        for field, (condition, value) in filters_map.items():
            if getattr(filters, field) is not None:
                conditions.append(condition)
                params.append(value)

        query = f"""
            SELECT 
                p.id, p.name, 
                p.author_id, u.email AS author_email, u.name AS author_name, u.avatar_id AS author_avatar_id, u.is_admin AS author_is_admin,
                p.category_id
            FROM projects p
            JOIN users u ON p.author_id = u.id
            WHERE {' AND '.join(conditions)}
        """

        cursor.execute(query, tuple(params))
        projects = cursor.fetchall()

        return [
            ProjectOut(
                id=proj["id"],
                name=proj["name"],
                author=UserOut(
                    id=proj["author_id"],
                    email=proj["author_email"],
                    name=proj["author_name"],
                    avatar_id=proj["author_avatar_id"]
                ),
                category_id=proj["category_id"]
            )
            for proj in projects
        ]

    async def update_project(self, project_id: int, project_data: ProjectUpdate, user_id: int,
                             is_admin: bool = False) -> ProjectOut:
        cursor = self.db.cursor()

        # Проверка существования проекта и прав доступа
        if not is_admin:
            cursor.execute("SELECT id FROM projects WHERE id = %s AND author_id = %s", (project_id, user_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found or not owned by user")
        else:
            cursor.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found")

        # Проверка категории
        if project_data.category_id:
            if not is_admin:
                cursor.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s",
                               (project_data.category_id, user_id))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Category not found or not owned by user")
            else:
                cursor.execute("SELECT id FROM categories WHERE id = %s", (project_data.category_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Category not found")

        # Формирование обновлений
        updates = {k: v for k, v in project_data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
        where_clause = "p.id = %s" if is_admin else "p.id = %s AND p.author_id = %s"

        set_values = list(updates.values())
        where_values = [project_id] if is_admin else [project_id, user_id]
        values = set_values + where_values

        # Обновление проекта с возвратом данных об авторе
        cursor.execute(
            f"""
            WITH updated_project AS (
                UPDATE projects p 
                SET {set_clause}
                WHERE {where_clause}
                RETURNING p.id, p.name, p.author_id, p.category_id
            )
            SELECT 
                up.id, up.name, 
                up.author_id, u.email AS author_email, u.name AS author_name, u.avatar_id AS author_avatar_id, u.is_admin AS author_is_admin,
                up.category_id
            FROM updated_project up
            JOIN users u ON up.author_id = u.id
            """,
            values
        )
        self.db.commit()
        updated_project = cursor.fetchone()

        # Формируем author как UserOut
        author = UserOut(
            id=updated_project["author_id"],
            email=updated_project["author_email"],
            name=updated_project["author_name"],
            avatar_id=updated_project["author_avatar_id"]
        )

        return ProjectOut(
            id=updated_project["id"],
            name=updated_project["name"],
            author=author,
            category_id=updated_project["category_id"]
        )


    async def delete_project(self, project_id: int, user_id: int, is_admin: bool = False):
        cursor = self.db.cursor()

        where_clause = "id = %s" if is_admin else "id = %s AND author_id = %s"
        values = [project_id] if is_admin else [project_id, user_id]

        cursor.execute(f"SELECT id FROM projects WHERE {where_clause}", values)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found or not owned by user")

        cursor.execute(f"DELETE FROM projects WHERE {where_clause}", values)
        self.db.commit()

    async def get_project_tasks_and_subtasks(self, project_id: int, user_id: int) -> ProjectTasksOut:
        cursor = self.db.cursor()

        # Проверка доступа: пользователь в проекте или автор проекта
        cursor.execute(
            """
            SELECT p.id, p.name, p.author_id, 
                   u.email AS author_email, u.name AS author_name, u.avatar_id AS author_avatar_id, u.is_admin AS author_is_admin
            FROM projects p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN project_users pu ON p.id = pu.project_id
            WHERE p.id = %s AND (pu.user_id = %s OR p.author_id = %s)
            """,
            (project_id, user_id, user_id)
        )
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        # Формируем author как UserOut
        author = UserOut(
            id=project["author_id"],
            email=project["author_email"],
            name=project["author_name"],
            avatar_id=project["author_avatar_id"]
        )

        # Получаем все задачи проекта
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
            WHERE t.project_id = %s
            """,
            (project_id,)
        )
        tasks = cursor.fetchall()

        # Получаем все подзадачи для задач проекта
        cursor.execute(
            """
            SELECT 
                s.id, s.task_id, s.name, s.description, s.due_date, s.priority, s.status,
                s.author_id, ua.email AS author_email, ua.name AS author_name, ua.avatar_id AS author_avatar_id, ua.is_admin AS author_is_admin,
                s.assignee_id, ub.email AS assignee_email, ub.name AS assignee_name, ub.avatar_id AS assignee_avatar_id, ub.is_admin AS assignee_is_admin
            FROM subtasks s
            JOIN users ua ON s.author_id = ua.id
            LEFT JOIN users ub ON s.assignee_id = ub.id
            WHERE s.task_id IN (SELECT id FROM tasks WHERE project_id = %s)
            """,
            (project_id,)
        )
        subtasks = cursor.fetchall()

        # Формируем список задач с подзадачами
        task_dict = {task["id"]: task for task in tasks}
        subtask_dict = {}
        for subtask in subtasks:
            task_id = subtask["task_id"]
            if task_id not in subtask_dict:
                subtask_dict[task_id] = []
            subtask_dict[task_id].append(subtask)

        tasks_with_subtasks = []
        for task in tasks:
            task_author = UserOut(
                id=task["author_id"],
                email=task["author_email"],
                name=task["author_name"],
                avatar_id=task["author_avatar_id"]
            )
            task_assignee = None
            if task["assignee_id"]:
                task_assignee = UserOut(
                    id=task["assignee_id"],
                    email=task["assignee_email"],
                    name=task["assignee_name"],
                    avatar_id=task["assignee_avatar_id"]
                )

            task_subtasks = []
            if task["id"] in subtask_dict:
                for subtask in subtask_dict[task["id"]]:
                    subtask_author = UserOut(
                        id=subtask["author_id"],
                        email=subtask["author_email"],
                        name=subtask["author_name"],
                        avatar_id=subtask["author_avatar_id"]
                    )
                    subtask_assignee = None
                    if subtask["assignee_id"]:
                        subtask_assignee = UserOut(
                            id=subtask["assignee_id"],
                            email=subtask["assignee_email"],
                            name=subtask["assignee_name"],
                            avatar_id=subtask["assignee_avatar_id"]
                        )
                    task_subtasks.append(SubtaskOut(
                        id=subtask["id"],
                        task_id=subtask["task_id"],
                        name=subtask["name"],
                        description=subtask["description"],
                        due_date=subtask["due_date"],
                        priority=subtask["priority"],
                        status=subtask["status"],
                        author=subtask_author,
                        assignee=subtask_assignee
                    ))

            tasks_with_subtasks.append(TaskWithSubtasksOut(
                id=task["id"],
                name=task["name"],
                description=task["description"],
                due_date=task["due_date"],
                priority=task["priority"],
                status=task["status"],
                author=task_author,
                assignee=task_assignee,
                project_id=task["project_id"],
                subtasks=task_subtasks
            ))

        return ProjectTasksOut(
            id=project["id"],
            name=project["name"],
            author=author,
            tasks=tasks_with_subtasks
        )