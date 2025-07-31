import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings

def get_db():
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

#DROP TABLE IF EXISTS projects CASCADE;
#DROP TABLE IF EXISTS categories CASCADE;
#DROP TABLE IF EXISTS subtasks CASCADE;
#DROP TABLE IF EXISTS tasks CASCADE;
#DROP TABLE IF EXISTS project_users CASCADE;
#DROP TABLE IF EXISTS users CASCADE;
#DROP TABLE IF EXISTS password_reset_codes CASCADE;


async def get_db_connection():
    return psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)


async def init_db():
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                avatar_id INT,
                is_admin BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                user_id INT REFERENCES users(id),
                color VARCHAR(7)
            );

            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                author_id INT REFERENCES users(id),
                category_id INT REFERENCES categories(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS project_users (
                project_id INT REFERENCES projects(id) ON DELETE CASCADE,
                user_id INT REFERENCES users(id),
                PRIMARY KEY (project_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                due_date DATE,
                priority VARCHAR(20),
                status VARCHAR(50),
                author_id INT REFERENCES users(id),
                assignee_id INT REFERENCES users(id),
                project_id INT REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS subtasks (
                id SERIAL PRIMARY KEY,
                task_id INT REFERENCES tasks(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                due_date DATE,
                priority VARCHAR(20),
                status VARCHAR(50),
                author_id INT REFERENCES users(id),
                assignee_id INT REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS password_reset_codes (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                code VARCHAR(6) NOT NULL,
                expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '10 minutes'
            );
            CREATE TABLE IF NOT EXISTS attachments (
                id SERIAL PRIMARY KEY,
                file_path VARCHAR(255) NOT NULL,
                uploaded_by INT REFERENCES users(id)
            );
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()