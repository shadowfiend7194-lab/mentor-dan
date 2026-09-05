from datetime import datetime

from database.connection import get_connection


# =========================================================
# ЛИМИТЫ ЦЕЛЕЙ
# =========================================================

FREE_MAX_GOALS = 1
PRO_MAX_GOALS = 3

# Старое имя оставляем для совместимости существующих импортов.
MAX_GOALS = PRO_MAX_GOALS


# =========================================================
# СОЗДАТЬ ЦЕЛЬ
# =========================================================

def create_goal(
    user_id,
    title,
    is_main=False,
):

    title = str(
        title or ""
    ).strip()

    if not title:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM goals
        WHERE user_id = ?
        AND active = 1
        """,
        (
            user_id,
        )
    )

    active_goal_count = cursor.fetchone()[0]

    # -----------------------------------------------------
    # ЛИМИТ
    # -----------------------------------------------------

    if active_goal_count >= MAX_GOALS:

        conn.close()

        return None

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

    # -----------------------------------------------------
    # ЕСЛИ ЭТО ГЛАВНАЯ ЦЕЛЬ
    # -----------------------------------------------------

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
            status,
            created_at,
            achieved_at,
            achievement_note,
            last_review_date,
            pro_status
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
        "status": row[4] or "active",
        "created_at": row[5],
        "achieved_at": row[6],
        "achievement_note": row[7],
        "last_review_date": row[8],
        "pro_status": row[9] or "active",
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
            status,
            created_at,
            achieved_at,
            achievement_note,
            last_review_date,
            pro_status
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
                "status": row[4] or "active",
                "created_at": row[5],
                "achieved_at": row[6],
                "achievement_note": row[7],
                "last_review_date": row[8],
                "pro_status": row[9] or "active",
            }
        )

    return goals


def get_user_goals_for_plan(
    user_id,
    include_frozen=False,
):
    """Возвращает цели с учётом PRO-статуса."""

    goals = get_user_goals(user_id)

    if include_frozen:
        return goals

    return [
        goal
        for goal in goals
        if goal.get("pro_status") != "frozen"
    ]


# =========================================================
# ОБНОВИТЬ ЦЕЛЬ
# =========================================================

def update_goal(
    user_id,
    goal_id,
    title,
):

    title = str(
        title or ""
    ).strip()

    if not title:
        return False

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

    changed = (
        cursor.rowcount > 0
    )

    conn.commit()
    conn.close()

    return changed


# =========================================================
# УДАЛИТЬ / ДЕАКТИВИРОВАТЬ ЦЕЛЬ
# =========================================================

def deactivate_goal(
    user_id,
    goal_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # СНАЧАЛА УБИРАЕМ СВЯЗЬ У ПРИВЫЧЕК
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE habits
        SET goal_id = NULL
        WHERE goal_id = ?
        AND user_id = ?
        """,
        (
            goal_id,
            user_id,
        )
    )

    # -----------------------------------------------------
    # ДЕАКТИВИРУЕМ ЦЕЛЬ
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT is_main
        FROM goals
        WHERE id = ? AND user_id = ? AND active = 1
        """,
        (goal_id, user_id),
    )
    was_main_row = cursor.fetchone()
    was_main = bool(was_main_row[0]) if was_main_row else False

    cursor.execute(
        """
        UPDATE goals
        SET
            active = 0,
            is_main = 0
        WHERE id = ?
        AND user_id = ?
        """,
        (
            goal_id,
            user_id,
        )
    )

    changed = cursor.rowcount > 0

    if changed and was_main:
        cursor.execute(
            """
            SELECT id
            FROM goals
            WHERE user_id = ? AND active = 1
            ORDER BY id ASC
            LIMIT 1
            """,
            (user_id,),
        )
        replacement = cursor.fetchone()
        if replacement:
            cursor.execute(
                "UPDATE goals SET is_main = 1 WHERE id = ? AND user_id = ? AND active = 1",
                (replacement[0], user_id),
            )

    conn.commit()
    conn.close()

    return changed


# =========================================================
# ОТМЕТИТЬ ПРОВЕРКУ ЦЕЛИ
# =========================================================

def mark_goal_reviewed(
    user_id,
    goal_id,
    review_date
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE goals
        SET last_review_date = ?
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            review_date,
            goal_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ДОСТИЧЬ ЦЕЛИ
# =========================================================

def achieve_goal(
    user_id,
    goal_id,
    achievement_note
):

    conn = get_connection()
    cursor = conn.cursor()

    achieved_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        UPDATE goals
        SET
            status = 'achieved',
            achieved_at = ?,
            achievement_note = ?,
            is_main = 0
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            achieved_at,
            achievement_note,
            goal_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()