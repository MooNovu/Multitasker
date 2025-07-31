from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.scheduler import start_scheduler
from app.routers import auth, profile, task, category, project, subtask, assigned, attachment
from app.database import init_db, get_db_connection

app = FastAPI(title="Multitasker")

# Подключение маршрутов
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(task.router, prefix="/task", tags=["task"])
app.include_router(category.router, prefix="/category", tags=["category"])
app.include_router(project.router, prefix="/project", tags=["project"])
app.include_router(subtask.router, prefix="/subtask", tags=["subtask"])
app.include_router(assigned.router, prefix="/assigned", tags=["assigned"])
#app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(attachment.router, prefix="/attachments", tags=["attachments"])

@app.on_event("startup")
async def startup():
    await init_db()
    start_scheduler()

    db = await get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE is_admin = TRUE LIMIT 1")
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO users (email, password, is_admin, name)
                VALUES (%s, %s, %s, %s)
                """,
                ("admin@example.com", "admin123", True, "Admin")
            )
            db.commit()
            print("Admin user created: admin@example.com / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)