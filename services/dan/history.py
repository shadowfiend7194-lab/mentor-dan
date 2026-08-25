from database.connection import get_connection


# =========================================================
# ДОБАВИТЬ СООБЩЕНИЕ В ИСТОРИЮ ДИАЛОГА
# =========================================================

def add_dan_message(
    user_id,
    role,
    content
):
    """
    Сохраняет сообщение пользователя или Дэна
    в историю диалога.
    
    role:
        user
        assistant
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO dan_messages (
            user_id,
            role,
            content
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            role,
            content
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ПОЛУЧИТЬ ПОСЛЕДНИЕ СООБЩЕНИЯ
# =========================================================

def get_dan_history(
    user_id,
    limit=10
):
    """
    Получает последние сообщения
    пользователя и Дэна.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            role,
            content,
            created_at
        FROM dan_messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit
        )
    )

    rows = cursor.fetchall()

    conn.close()

    rows.reverse()

    history = []

    for row in rows:

        history.append({
            "role": row[0],
            "content": row[1],
            "created_at": row[2]
        })

    return history


# =========================================================
# ОЧИСТИТЬ ИСТОРИЮ
# =========================================================

def clear_dan_history(
    user_id
):
    """
    Полностью очищает историю диалога Дэна
    конкретного пользователя.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM dan_messages
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()