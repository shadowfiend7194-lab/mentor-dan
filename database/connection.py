import sqlite3

from config import DATABASE_URL


def get_connection():
    """
    Создаёт подключение к базе данных.
    """

    return sqlite3.connect(
        DATABASE_URL
    )