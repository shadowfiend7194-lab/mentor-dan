from datetime import date, timedelta

from database.connection import get_connection
from database.habits import (
    get_user_habits,
    is_habit_scheduled_on_date,
)


# =========================================================
# ВЫПОЛНЕНИЕ ОДНОЙ ПРИВЫЧКИ ЗА ПЕРИОД
# =========================================================

def get_habit_completion_stats(
    habit,
    start_date,
    end_date,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            date,
            completed
        FROM habit_logs
        WHERE habit_id = ?
        AND date >= ?
        AND date <= ?
        """,
        (
            habit["id"],
            start_date.isoformat(),
            end_date.isoformat(),
        )
    )

    rows = cursor.fetchall()

    conn.close()

    logs = {
        row[0]: bool(row[1])
        for row in rows
    }

    scheduled = 0
    completed = 0

    current = start_date

    while current <= end_date:
        if is_habit_scheduled_on_date(
            habit,
            current,
        ):
            scheduled += 1

            if logs.get(
                current.isoformat(),
                False,
            ):
                completed += 1

        current += timedelta(days=1)

    percentage = (
        round(
            completed / scheduled * 100
        )
        if scheduled
        else 0
    )

    return {
        "scheduled": scheduled,
        "completed": completed,
        "percentage": percentage,
    }


# =========================================================
# АНАЛИЗ ПРИВЫЧЕК
# =========================================================

def get_habit_analysis(user_id):
    habits = get_user_habits(user_id)

    today = date.today()

    current_start = (
        today - timedelta(days=6)
    )

    previous_start = (
        today - timedelta(days=13)
    )

    previous_end = (
        today - timedelta(days=7)
    )

    result = []

    for habit in habits:
        current = get_habit_completion_stats(
            habit,
            current_start,
            today,
        )

        previous = get_habit_completion_stats(
            habit,
            previous_start,
            previous_end,
        )

        change = (
            current["percentage"]
            - previous["percentage"]
        )

        result.append(
            {
                "name": habit["name"],
                "type": habit["habit_type"],
                "formed": habit["formed"],
                "controlled": habit["controlled"],
                "current_week": current,
                "previous_week": previous,
                "change_percentage_points": change,
            }
        )

    return result


# =========================================================
# ТРЕНДЫ CHECK-IN
# =========================================================

def get_checkin_trends(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()

    start_date = (
        today - timedelta(days=13)
    )

    # В текущей базе используются именно эти поля:
    #
    # morning_energy
    # morning_sleep
    # morning_mood
    # morning_stress
    # evening_score

    cursor.execute(
        """
        SELECT
            date,
            morning_energy,
            morning_sleep,
            morning_mood,
            morning_stress,
            evening_score
        FROM checkins
        WHERE user_id = ?
        AND date >= ?
        AND date <= ?
        ORDER BY date ASC
        """,
        (
            user_id,
            start_date.isoformat(),
            today.isoformat(),
        )
    )

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return {
            "days": [],
            "current": {},
            "previous": {},
            "changes": {},
        }

    days = []

    for row in rows:
        days.append(
            {
                "date": row[0],
                "energy": row[1],
                "sleep": row[2],
                "mood": row[3],
                "stress": row[4],
                "evening_score": row[5],
            }
        )

    current_start = (
        today - timedelta(days=6)
    ).isoformat()

    current_rows = [
        row
        for row in days
        if row["date"] >= current_start
    ]

    previous_rows = [
        row
        for row in days
        if row["date"] < current_start
    ]

    def average(rows, key):
        values = [
            row[key]
            for row in rows
            if row[key] is not None
        ]

        if not values:
            return None

        return round(
            sum(values) / len(values),
            1,
        )

    current = {
        "energy": average(
            current_rows,
            "energy",
        ),
        "sleep": average(
            current_rows,
            "sleep",
        ),
        "mood": average(
            current_rows,
            "mood",
        ),
        "stress": average(
            current_rows,
            "stress",
        ),
        "evening_score": average(
            current_rows,
            "evening_score",
        ),
    }

    previous = {
        "energy": average(
            previous_rows,
            "energy",
        ),
        "sleep": average(
            previous_rows,
            "sleep",
        ),
        "mood": average(
            previous_rows,
            "mood",
        ),
        "stress": average(
            previous_rows,
            "stress",
        ),
        "evening_score": average(
            previous_rows,
            "evening_score",
        ),
    }

    changes = {}

    for key in current:
        if (
            current[key] is not None
            and previous[key] is not None
        ):
            changes[key] = round(
                current[key] - previous[key],
                1,
            )

    return {
        "days": days,
        "current": current,
        "previous": previous,
        "changes": changes,
    }