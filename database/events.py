from datetime import datetime

from database.connection import get_connection


# =========================================================
# ДОБАВИТЬ СОБЫТИЕ
# =========================================================

def add_event(
    user_id,
    event_type,
    title,
    description
):

    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO user_events
        (
            user_id,
            event_type,
            title,
            description,
            created_at
        )

        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            event_type,
            title,
            description,
            created_at
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ПОЛУЧИТЬ СОБЫТИЯ
# =========================================================

def get_user_events(
    user_id,
    limit=5
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            event_type,
            title,
            description,
            created_at

        FROM user_events

        WHERE user_id = ?

        ORDER BY created_at DESC

        LIMIT ?
        """,
        (
            user_id,
            limit,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return rows