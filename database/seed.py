from database.db import get_connection
from database.models import create_tables


def seed_database():
    create_tables()

    conn = get_connection()
    cursor = conn.cursor()

    rooms = [
        ("603", "Robotics Lab", 6),
        ("705", "AI Lab", 7),
        ("502", "Software Lab", 5),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO rooms
        (room_number, room_name, floor)
        VALUES (?, ?, ?)
        """,
        rooms,
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed_database()
    print("Database created successfully!")