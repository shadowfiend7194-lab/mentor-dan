from datetime import datetime

from database.connection import get_connection


# =========================================================
# СОЗДАТЬ ЦЕЛЬ
# =========================================================

def create_goal(
    user_id,
    title,
    is_main=False,
):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO goals
        (
            user_id,
            title,
            is_main,
            active,
            created_at
        )
        VALUES (?, ?, ?, 1, ?)
        """,
        (
            user_id,
            title,
            1 if is_main else 0,
            now,
        )
    )

    goal_id = cursor.lastrowid

    # Если это главная цель —
    # снимаем статус главной с остальных.
    if is_main:

        cursor.execute(
            """
            UPDATE goals
            SET is_main = 0
            WHERE user_id = ?
            AND id != ?
            """,
            (
                user_id,
                goal_id,
            )
        )

    conn.commit()
    conn.close()

    return goal_id


# =========================================================
# ПОЛУЧИТЬ ГЛАВНУЮ ЦЕЛЬ
# =========================================================

def get_main_goal(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            is_main,
            active,
            created_at
        FROM goals
        WHERE user_id = ?
        AND is_main = 1
        AND active = 1
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            user_id,
        )
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "is_main": bool(row[2]),
        "active": bool(row[3]),
        "created_at": row[4],
    }


# =========================================================
# ПОЛУЧИТЬ ВСЕ ЦЕЛИ
# =========================================================

def get_user_goals(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            is_main,
            active,
            created_at
        FROM goals
        WHERE user_id = ?
        AND active = 1
        ORDER BY is_main DESC, id ASC
        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    goals = []

    for row in rows:

        goals.append(
            {
                "id": row[0],
                "title": row[1],
                "is_main": bool(row[2]),
                "active": bool(row[3]),
                "created_at": row[4],
            }
        )

    return goals


# =========================================================
# ОБНОВИТЬ ЦЕЛЬ
# =========================================================

def update_goal(
    user_id,
    goal_id,
    title,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE goals
        SET title = ?
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            title,
            goal_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# УДАЛИТЬ / ДЕАКТИВИРОВАТЬ ЦЕЛЬ
# =========================================================

def deactivate_goal(
    user_id,
    goal_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE goals
        SET active = 0,
            is_main = 0
        WHERE id = ?
        AND user_id = ?
        """,
        (
            goal_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()