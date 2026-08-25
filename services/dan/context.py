from database.checkins import (
    get_today_checkin,
    get_recent_checkins,
)

from database.goals import (
    get_user_goals,
)

from database.progress import (
    get_progress_summary,
)

from database.dan.conversations import (
    get_recent_dan_messages,
)

from database.habits import (
    get_user_habits,
)

from services.dan.memory import (
    get_user_memories,
)

from services.dan.habit_trends import (
    get_habit_trends,
)


# =========================================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def get_user_profile(user_id):

    from database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            name,
            age,
            wake_time,
            sleep_time
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return {}

    return {
        "name": row[0],
        "age": row[1],
        "wake_time": row[2],
        "sleep_time": row[3],
    }


# =========================================================
# КОНТЕКСТ ПРИВЫЧЕК
# =========================================================

def get_user_habits_context(user_id):

    habits = get_user_habits(
        user_id
    )

    result = []

    for habit in habits:

        result.append(
            {
                "id": habit.get("id"),
                "name": habit.get("name"),
                "type": habit.get("habit_type"),
                "frequency": habit.get("frequency"),

                "formed": habit.get(
                    "formed",
                    False,
                ),

                "controlled": habit.get(
                    "controlled",
                    False,
                ),
            }
        )

    return result


# =========================================================
# КОНТЕКСТ CHECK-IN
# =========================================================

def get_recent_checkins_context(
    user_id,
    limit=7,
):

    rows = get_recent_checkins(
        user_id,
        limit=limit,
    )

    result = []

    for row in rows:

        result.append(
            {
                "date": row[0],

                "energy": row[1],
                "sleep": row[2],
                "mood": row[3],
                "stress": row[4],

                "evening_score": row[5],

                "evening_problem": row[6],
                "evening_positive": row[7],
                "evening_improve": row[8],
            }
        )

    return result


# =========================================================
# СРЕДНЕЕ ЗНАЧЕНИЕ
# =========================================================

def calculate_average(values):

    values = [
        value
        for value in values
        if value is not None
    ]

    if not values:
        return None

    return round(
        sum(values) / len(values),
        1,
    )


# =========================================================
# ТРЕНДЫ CHECK-IN
# =========================================================

def get_checkin_trends_context(
    user_id,
    limit=7,
):

    rows = get_recent_checkins_context(
        user_id,
        limit=limit,
    )

    if not rows:
        return {}

    metrics = (
        "energy",
        "sleep",
        "mood",
        "stress",
        "evening_score",
    )

    trends = {}

    for metric in metrics:

        values = [
            row.get(metric)
            for row in rows
            if row.get(metric) is not None
        ]

        if not values:
            continue

        average = calculate_average(
            values
        )

        latest = values[0]

        if len(values) >= 2:

            previous = calculate_average(
                values[1:]
            )

            change = round(
                latest - previous,
                1,
            )

        else:

            previous = None
            change = None

        if change is None:

            trend = "unknown"

        elif change >= 1:

            trend = "up"

        elif change <= -1:

            trend = "down"

        else:

            trend = "stable"

        trends[metric] = {
            "today": latest,
            "average": average,
            "previous_average": previous,
            "change": change,
            "trend": trend,
        }

    return {
        "days_analyzed": len(rows),
        "metrics": trends,
        "history": rows,
    }


# =========================================================
# СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ СЕГОДНЯ
# =========================================================

def get_current_state(user_id):

    row = get_today_checkin(
        user_id
    )

    if not row:
        return {}

    return {
        "date": row[0],

        "energy": row[1],
        "sleep": row[2],
        "mood": row[3],
        "stress": row[4],

        "evening_score": row[5],

        "evening_problem": row[6],
        "evening_positive": row[7],
        "evening_improve": row[8],
    }


# =========================================================
# СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ
# =========================================================

def get_user_statistics(user_id):

    stats = get_progress_summary(
        user_id
    )

    return {
        "best_streak": stats.get(
            "best_streak",
            0,
        ),

        "week_completed": stats.get(
            "week_completed",
            0,
        ),

        "week_total": stats.get(
            "week_total",
            0,
        ),

        "energy": stats.get(
            "energy",
            0,
        ),

        "sleep": stats.get(
            "sleep",
            0,
        ),

        "mood": stats.get(
            "mood",
            0,
        ),

        "stress": stats.get(
            "stress",
            0,
        ),

        "evening_score": stats.get(
            "evening_score",
            0,
        ),
    }


# =========================================================
# КОНТЕКСТ ДИАЛОГА ДЭНА
# =========================================================

def get_conversation_context(
    user_id,
    limit=10,
):

    rows = get_recent_dan_messages(
        user_id,
        limit=limit,
    )

    result = []

    for row in rows:

        if isinstance(row, dict):

            result.append(row)

            continue

        if len(row) >= 3:

            result.append(
                {
                    "role": row[0],
                    "content": row[1],
                    "created_at": row[2],
                }
            )

        elif len(row) >= 2:

            result.append(
                {
                    "role": row[0],
                    "content": row[1],
                }
            )

    return result


# =========================================================
# ПОЛНЫЙ КОНТЕКСТ ДЭНА
# =========================================================

def get_dan_context(user_id):

    return {

        # -------------------------------------------------
        # ПРОФИЛЬ
        # -------------------------------------------------

        "profile": get_user_profile(
            user_id
        ),

        # -------------------------------------------------
        # ЦЕЛИ
        # -------------------------------------------------

        "goals": get_user_goals(
            user_id
        ),

        # -------------------------------------------------
        # АКТИВНЫЕ ПРИВЫЧКИ
        # -------------------------------------------------

        "habits": get_user_habits_context(
            user_id
        ),

        # -------------------------------------------------
        # АНАЛИТИКА ПРИВЫЧЕК
        # -------------------------------------------------

        "habit_trends": get_habit_trends(
            user_id
        ),

        # -------------------------------------------------
        # ТЕКУЩЕЕ СОСТОЯНИЕ
        # -------------------------------------------------

        "current_state": get_current_state(
            user_id
        ),

        # -------------------------------------------------
        # ОБЩАЯ СТАТИСТИКА
        # -------------------------------------------------

        "statistics": get_user_statistics(
            user_id
        ),

        # -------------------------------------------------
        # ПАМЯТЬ
        # -------------------------------------------------

        "memories": get_user_memories(
            user_id,
            limit=30,
        ),

        # -------------------------------------------------
        # ДИАЛОГ
        # -------------------------------------------------

        "conversation": get_conversation_context(
            user_id,
            limit=10,
        ),
    }

