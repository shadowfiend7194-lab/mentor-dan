from database.connection import get_connection
from services.subscription import user_has_pro


# =========================================================
# ПРОВЕРКА PRO
# =========================================================

def is_pro_user(user_id):
    """
    True только при реально активном PRO.
    """

    try:

        return bool(
            user_has_pro(user_id)
        )

    except Exception as error:

        print(
            f"[PRO HABITS] "
            f"Ошибка проверки PRO: {error}"
        )

        return False


# =========================================================
# ПОЛУЧИТЬ ЦЕЛИ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def get_available_goals(user_id):
    """
    Возвращает активные цели пользователя,
    доступные для PRO-связи с привычками.
    """

    if not is_pro_user(user_id):

        return []

    from database.goals import (
        get_user_goals,
    )

    goals = get_user_goals(
        user_id
    )

    result = []

    for goal in goals:

        if not isinstance(
            goal,
            dict,
        ):
            continue

        goal_id = goal.get(
            "id"
        )

        if goal_id is None:
            continue

        result.append(
            {
                "id": goal_id,

                "title": (
                    goal.get("title")
                    or goal.get("name")
                    or "Без названия"
                ),

                "is_main": bool(
                    goal.get(
                        "is_main",
                        False,
                    )
                ),

                "status": (
                    goal.get("status")
                    or "active"
                ),
            }
        )

    return result


# =========================================================
# ПОЛУЧИТЬ ПРИВЫЧКУ
# =========================================================

def get_habit(
    user_id,
    habit_id,
):
    """
    Возвращает привычку пользователя
    вместе с PRO-полями.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            habit_type,
            frequency,
            schedule_days,
            created_at,
            formed,
            formed_at,
            last_review_date,
            controlled,
            controlled_at,
            difficulty,
            motivation,
            goal_id
        FROM habits
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        LIMIT 1
        """,
        (
            habit_id,
            user_id,
        ),
    )

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    return {
        "id": row[0],
        "name": row[1],
        "habit_type": row[2],
        "frequency": row[3],
        "schedule_days": row[4],
        "created_at": row[5],
        "formed": bool(row[6]),
        "formed_at": row[7],
        "last_review_date": row[8],
        "controlled": bool(row[9]),
        "controlled_at": row[10],
        "difficulty": row[11],
        "motivation": row[12],
        "goal_id": row[13],
    }


# =========================================================
# ПОЛУЧИТЬ PRO-ДАННЫЕ ПРИВЫЧКИ
# =========================================================

def get_habit_pro_data(
    user_id,
    habit_id,
):
    """
    Возвращает расширенные данные привычки.

    Если PRO не активен —
    возвращается пустой словарь.
    """

    if not is_pro_user(user_id):

        return {}

    habit = get_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return {}

    return {
        "difficulty": habit.get(
            "difficulty"
        ),

        "motivation": habit.get(
            "motivation"
        ),

        "goal_id": habit.get(
            "goal_id"
        ),
    }


# =========================================================
# СОХРАНИТЬ ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ
# =========================================================

def update_habit_pro_data(
    user_id,
    habit_id,
    difficulty=None,
    motivation=None,
):
    """
    Сохраняет сложность и мотивацию привычки.
    """

    if not is_pro_user(user_id):

        return False

    habit = get_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return False

    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    values = []

    if difficulty is not None:

        updates.append(
            "difficulty = ?"
        )

        values.append(
            difficulty
        )

    if motivation is not None:

        updates.append(
            "motivation = ?"
        )

        values.append(
            motivation
        )

    if not updates:

        conn.close()

        return True

    values.extend(
        [
            habit_id,
            user_id,
        ]
    )

    cursor.execute(
        f"""
        UPDATE habits
        SET {", ".join(updates)}
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        tuple(values),
    )

    conn.commit()

    changed = (
        cursor.rowcount > 0
    )

    conn.close()

    return changed


# =========================================================
# ПРИВЯЗАТЬ ПРИВЫЧКУ К ЦЕЛИ
# =========================================================

def set_habit_goal(
    user_id,
    habit_id,
    goal_id,
):
    """
    Привязывает привычку к цели.

    Проверяется:
    - активен ли PRO;
    - существует ли привычка;
    - принадлежит ли привычка пользователю;
    - существует ли цель;
    - принадлежит ли цель пользователю.
    """

    if not is_pro_user(user_id):

        return False

    habit = get_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return False

    goals = get_available_goals(
        user_id
    )

    valid_goal_ids = {
        goal["id"]
        for goal in goals
    }

    if goal_id not in valid_goal_ids:

        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET goal_id = ?
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            goal_id,
            habit_id,
            user_id,
        ),
    )

    changed = (
        cursor.rowcount > 0
    )

    conn.commit()
    conn.close()

    return changed


# =========================================================
# ОТВЯЗАТЬ ПРИВЫЧКУ ОТ ЦЕЛИ
# =========================================================

def remove_habit_goal(
    user_id,
    habit_id,
):
    """
    Полностью убирает связь привычки
    с целью.

    Сама привычка не удаляется.
    Сама цель не удаляется.
    """

    if not is_pro_user(user_id):

        return False

    habit = get_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET goal_id = NULL
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            habit_id,
            user_id,
        ),
    )

    changed = (
        cursor.rowcount > 0
    )

    conn.commit()
    conn.close()

    return changed


# =========================================================
# ПОЛУЧИТЬ ЦЕЛЬ ПРИВЫЧКИ
# =========================================================

def get_habit_goal(
    user_id,
    habit_id,
):
    """
    Возвращает цель,
    к которой привязана привычка.

    Если связи нет — None.
    """

    if not is_pro_user(user_id):

        return None

    habit = get_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return None

    goal_id = habit.get(
        "goal_id"
    )

    if goal_id is None:

        return None

    goals = get_available_goals(
        user_id
    )

    for goal in goals:

        if goal["id"] == goal_id:

            return goal

    return None


# =========================================================
# ПОЛУЧИТЬ ВСЕ ПРИВЫЧКИ С ЦЕЛЯМИ
# =========================================================

def get_habits_with_goals(
    user_id,
):
    """
    Возвращает все привычки пользователя
    вместе с их PRO-связями с целями.

    Это будет использоваться дальше
    для расчёта прогресса целей.
    """

    if not is_pro_user(user_id):

        return []

    from database.habits import (
        get_user_habits,
    )

    habits = get_user_habits(
        user_id
    )

    goals = get_available_goals(
        user_id
    )

    goals_by_id = {
        goal["id"]: goal
        for goal in goals
    }

    result = []

    for habit in habits:

        item = dict(
            habit
        )

        # На случай, если старая версия
        # get_user_habits() ещё не возвращает goal_id,
        # берём его напрямую из базы.

        if item.get("goal_id") is None:

            full_habit = get_habit(
                user_id,
                item.get("id")
            )

            if full_habit:

                item["goal_id"] = (
                    full_habit.get(
                        "goal_id"
                    )
                )

                item["difficulty"] = (
                    full_habit.get(
                        "difficulty"
                    )
                )

                item["motivation"] = (
                    full_habit.get(
                        "motivation"
                    )
                )

        goal_id = item.get(
            "goal_id"
        )

        item["goal"] = (
            goals_by_id.get(
                goal_id
            )
            if goal_id is not None
            else None
        )

        result.append(
            item
        )

    return result
