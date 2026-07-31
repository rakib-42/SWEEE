import sqlite3

from core.config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# Teachers
# ==========================

def search_teacher(keyword):
    conn = get_connection()
    cursor = conn.cursor()

    keyword = keyword.strip()

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE
            CAST(id AS TEXT) = ?
            OR LOWER(name) LIKE LOWER(?)
            OR LOWER(designation) LIKE LOWER(?)
            OR LOWER(department) LIKE LOWER(?)
            OR LOWER(email) LIKE LOWER(?)
    """, (
        keyword,
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ))

    results = cursor.fetchall()
    conn.close()

    return results


# ==========================
# Places
# ==========================

def search_place(keyword):
    conn = get_connection()
    cursor = conn.cursor()

    keyword = keyword.strip().lower()

    # 1. Exact name
    cursor.execute("""
        SELECT *
        FROM places
        WHERE LOWER(name)=?
    """, (keyword,))

    results = cursor.fetchall()

    # 2. Partial name
    if not results:
        cursor.execute("""
            SELECT *
            FROM places
            WHERE LOWER(name) LIKE ?
        """, (f"%{keyword}%",))

        results = cursor.fetchall()

    conn.close()

    return results

# ==========================
# Robot
# ==========================

def get_robot_event(event):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM robot
        WHERE LOWER(event) = LOWER(?)
    """, (event,))

    result = cursor.fetchone()
    conn.close()

    return result