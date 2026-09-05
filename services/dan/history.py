"""
Совместимый фасад истории Дэна.

Каноническое хранилище находится в database.dan.conversations.
Старый вариант обращался к несуществующему столбцу content.
"""

from database.dan.conversations import (
    save_dan_message,
    get_dan_messages,
    get_recent_dan_messages,
    clear_dan_messages,
)


def add_dan_message(user_id, role, content):
    return save_dan_message(
        user_id=user_id,
        role=role,
        message=content,
    )


def get_dan_history(user_id, limit=10):
    rows = get_dan_messages(user_id, limit=limit)
    return [
        {
            "role": row[0],
            "content": row[1],
            "created_at": row[2],
        }
        for row in rows
    ]


def clear_dan_history(user_id):
    return clear_dan_messages(user_id)
