from database.db import get_connection


def find_room(room_number):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT room_name, floor
        FROM rooms
        WHERE room_number = ?
    """, (room_number,))

    result = cursor.fetchone()

    conn.close()

    if result:
        return {
            "room_number": room_number,
            "room_name": result[0],
            "floor": result[1]
        }

    return None