from datetime import datetime

from database.connection import get_connection


# =========================================================
# СОХРАНЕНИЕ СООБЩЕНИЯ ДЭНА
# =========================================================

def save_dan_message(
    user_id,
    role,
    message,
):
    """
    role:
        user      — сообщение пользователя
        assistant — ответ Дэна
    """

    if not message:
        return

    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO dan_messages
        (
            user_id,
            role,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            role,
            message,
            created_at,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ПОЛУЧЕНИЕ ИСТОРИИ ДИАЛОГА
# =========================================================

def get_dan_messages(
    user_id,
    limit=10,
):
    """
    Возвращает последние сообщения пользователя и Дэна.

    В результате:
        role
        message
        created_at

    Сообщения возвращаются в обычном порядке диалога:
    от старых к новым.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            role,
            message,
            created_at
        FROM dan_messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    # В базе новые сообщения идут первыми.
    # Для AI нужен обычный порядок диалога.
    rows.reverse()

    return rows


# =========================================================
# ПОЛУЧЕНИЕ ПОСЛЕДНИХ СООБЩЕНИЙ
# =========================================================

def get_recent_dan_messages(
    user_id,
    limit=10,
):
    return get_dan_messages(
        user_id,
        limit,
    )


# =========================================================
# КОЛИЧЕСТВО СООБЩЕНИЙ
# =========================================================

def get_dan_message_count(
    user_id,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM dan_messages
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    result = cursor.fetchone()

    conn.close()

    return (
        result[0]
        if result
        else 0
    )


# =========================================================
# ОЧИСТКА ИСТОРИИ ДИАЛОГА
# =========================================================

def clear_dan_messages(
    user_id,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM dan_messages
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    conn.commit()
    conn.close()