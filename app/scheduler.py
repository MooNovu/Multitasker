from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import get_db_connection
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor

scheduler = AsyncIOScheduler()

async def check_task_deadlines():
    conn = await get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE tasks
            SET status = 'просрочена'
            WHERE due_date < %s AND status != 'выполнена'
            """,
            (date.today(),)
        )
        conn.commit()
    except Exception as e:
        print(f"Error checking deadlines: {e}")
        conn.rollback()
    finally:
        conn.close()

async def check_subtask_deadlines():
    conn = await get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE subtasks
            SET status = 'просрочена'
            WHERE due_date < %s AND status != 'выполнена'
            """,
            (date.today(),)
        )
        conn.commit()
    except Exception as e:
        print(f"Error checking deadlines: {e}")
        conn.rollback()
    finally:
        conn.close()

# Запускаем задачу каждый день в полночь
scheduler.add_job(check_task_deadlines, 'cron', hour=0, minute=0)
scheduler.add_job(check_subtask_deadlines, 'cron', hour=0, minute=0)

def start_scheduler():
    scheduler.start()