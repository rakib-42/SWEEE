import sqlite3

conn = sqlite3.connect("database/sweee.db")
cursor = conn.cursor()

tables = ["teachers", "places", "robot"]

for table in tables:
    print(f"\n===== {table.upper()} =====")

    cursor.execute(f"SELECT * FROM {table}")

    rows = cursor.fetchall()

    for row in rows:
        print(row)

conn.close()