import psycopg2
from config import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    with get_connection() as conn, conn.cursor() as cur:
        # Create resources table if not exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id SERIAL PRIMARY KEY,
            semester INT NOT NULL,
            course TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            uploader_id BIGINT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
        """)
        # Create users table if not exists; admin is just a user with is_admin=True
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            is_admin BOOLEAN DEFAULT FALSE
        )
        """)
        conn.commit()

def add_resource(semester, course, resource_type, file_id, file_name, uploader_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO resources (semester, course, resource_type, file_id, file_name, uploader_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (semester, course, resource_type, file_id, file_name, uploader_id))
        conn.commit()

def get_resources(semester, course, resource_type):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
        SELECT id, file_name, file_id FROM resources
        WHERE semester=%s AND course=%s AND resource_type=%s
        ORDER BY uploaded_at DESC
        """, (semester, course, resource_type))
        return cur.fetchall()

def get_resource_by_id(resource_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
        SELECT file_id, file_name FROM resources WHERE id=%s
        """, (resource_id,))
        return cur.fetchone()

def delete_resource(resource_id):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM resources WHERE id=%s", (resource_id,))
        conn.commit()

# --- User management (admin counts as a user) ---

def add_user(user_id, username=None, is_admin=False):
    """
    Adds a user if not exists. If exists, updates username. 
    If is_admin is ever True for a user, it stays True.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO users (user_id, username, is_admin)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET username=EXCLUDED.username,
            is_admin=(users.is_admin OR EXCLUDED.is_admin)
        """, (user_id, username, is_admin))
        conn.commit()

def get_all_user_ids():
    """
    Returns all user IDs (admins included).
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]

def is_admin(user_id):
    """
    Returns True if the user is admin, else False.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT is_admin FROM users WHERE user_id=%s", (user_id,))
        result = cur.fetchone()
        return result is not None and result[0] is True

def set_admin(user_id, admin=True):
    """
    Set is_admin for a user.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET is_admin=%s WHERE user_id=%s",
            (admin, user_id)
        )
        conn.commit()
