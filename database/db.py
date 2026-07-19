import sqlite3

DATABASE_NAME = "database/sweee.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)