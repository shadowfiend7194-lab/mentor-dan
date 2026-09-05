from database.checkins import get_today_checkin, get_recent_checkins
from database.goals import get_user_goals
from database.progress import get_progress_summary
from database.dan.conversations import get_recent_dan_messages
from database.habits import get_user_habits
from services.dan.memory import get_user_memories
from services.dan.habit_trends import get_habit_trends


def get_user_profile(user_id):
    from database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, age, wake_time, sleep_time
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
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


def _goal_context(user_id):
    result = []
    for goal in get_user_goals(user_id):
        result.append(
            {
                "id": goal.get("id"),
                "title": goal.get("title"),
                "main": bool(goal.get("is_main")),
                "status": goal.get("status") or "active",
                "pro_status": goal.get("pro_status") or "active",
            }
        )
    return result


def _habit_context(user_id):
    goals = {
        goal.get("id"): goal.get("title")
        for goal in get_user_goals(user_id)
    }

    result = []
    for habit in get_user_habits(user_id):
        result.append(
            {
                "id": habit.get("id"),
                "name": habit.get("name"),
                "type": habit.get("habit_type"),
                "frequency": habit.get("frequency"),
                "difficulty": habit.get("difficulty"),
                "goal": goals.get(habit.get("goal_id")) or "Для себя",
                "formed": bool(habit.get("formed")),
                "controlled": bool(habit.get("controlled")),
                "pro_status": habit.get("pro_status") or "active",
            }
        )
    return result


def get_recent_checkins_context(user_id, limit=7):
    rows = get_recent_checkins(user_id, limit=limit)
    return [
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
        for row in rows
    ]


def calculate_average(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def get_checkin_trends_context(user_id, limit=7):
    rows = get_recent_checkins_context(user_id, limit=limit)
    if not rows:
        return {}

    metrics = ("energy", "sleep", "mood", "stress", "evening_score")
    trends = {}

    for metric in metrics:
        values = [
            row.get(metric)
            for row in rows
            if row.get(metric) is not None
        ]
        if not values:
            continue

        latest = values[0]
        average = calculate_average(values)

        previous = (
            calculate_average(values[1:])
            if len(values) >= 2
            else None
        )

        change = (
            round(latest - previous, 1)
            if previous is not None
            else None
        )

        if change is None:
            trend = "unknown"
        elif change >= 1:
            trend = "up"
        elif change <= -1:
            trend = "down"
        else:
            trend = "stable"

        trends[metric] = {
            "latest": latest,
            "average": average,
            "change": change,
            "trend": trend,
        }

    return {
        "days": len(rows),
        "metrics": trends,
    }


def get_current_state(user_id):
    row = get_today_checkin(user_id)
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


def get_user_statistics(user_id):
    stats = get_progress_summary(user_id)
    return {
        "best_streak": stats.get("best_streak", 0),
        "week_completed": stats.get("week_completed", 0),
        "week_total": stats.get("week_total", 0),
        "energy": stats.get("energy", 0),
        "sleep": stats.get("sleep", 0),
        "mood": stats.get("mood", 0),
        "stress": stats.get("stress", 0),
        "evening_score": stats.get("evening_score", 0),
    }


def get_conversation_context(user_id, limit=6):
    rows = get_recent_dan_messages(user_id, limit=limit)
    result = []

    for row in rows:
        if isinstance(row, dict):
            role = row.get("role")
            content = row.get("content") or row.get("message")
        else:
            role = row[0] if len(row) > 0 else None
            content = row[1] if len(row) > 1 else None

        if role and content:
            result.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    return result


def get_memories_context(user_id, limit=6):
    memories = get_user_memories(user_id, limit=limit)
    result = []

    for memory in memories:
        if isinstance(memory, dict):
            key = memory.get("key")
            value = memory.get("value")
            importance = memory.get("importance")
        else:
            key = memory[0] if len(memory) > 0 else None
            value = memory[1] if len(memory) > 1 else None
            importance = memory[2] if len(memory) > 2 else None

        if key and value:
            result.append(
                {
                    "key": key,
                    "value": value,
                    "importance": importance,
                }
            )

    return result


def _compact_habit_trends(user_id):
    """
    habit_trends остаётся аналитическим движком проекта,
    но в prompt передаётся только полезная выжимка.
    """
    try:
        data = get_habit_trends(user_id)
    except Exception as error:
        print(
            f"[DAN CONTEXT] habit trends unavailable: {error}"
        )
        return {}

    habits = []
    for habit in data.get("habits", []):
        current = habit.get("current_week", {})
        previous = habit.get("previous_week", {})

        habits.append(
            {
                "name": habit.get("name"),
                "type": habit.get("type"),
                "current": current.get("completion_rate"),
                "previous": previous.get("completion_rate"),
                "change": habit.get("change_percentage_points"),
                "streak": habit.get("current_streak", 0),
            }
        )

    return {
        "current_rate": data.get("current_week", {}).get(
            "completion_rate"
        ),
        "previous_rate": data.get("previous_week", {}).get(
            "completion_rate"
        ),
        "change": data.get("overall", {}).get(
            "change_percentage_points"
        ),
        "trend": data.get("overall", {}).get("trend"),
        "strongest_improvements": data.get(
            "strongest_improvements", []
        )[:3],
        "strongest_declines": data.get(
            "strongest_declines", []
        )[:3],
        "habits": habits[:6],
    }


def get_context_for_level(user_id, context_level):
    """
    Лёгкий контекст используется почти всегда.
    Глубокая аналитика подключается только для персонального
    сообщения/анализа.
    """
    profile = get_user_profile(user_id)

    if context_level == "conversation":
        return {
            "profile": {
                "name": profile.get("name")
            } if profile.get("name") else {},
            "goals": [],
            "habits": [],
            "habit_trends": {},
            "current_state": {},
            "statistics": {},
            "memories": get_memories_context(user_id, limit=3),
            "conversation": get_conversation_context(user_id, limit=6),
        }

    if context_level == "personal":
        return {
            "profile": profile,
            "goals": _goal_context(user_id),
            "habits": _habit_context(user_id),
            "habit_trends": _compact_habit_trends(user_id),
            "current_state": get_current_state(user_id),
            "statistics": get_user_statistics(user_id),
            "memories": get_memories_context(user_id, limit=6),
            "conversation": get_conversation_context(user_id, limit=6),
        }

    if context_level == "analysis":
        return {
            "profile": profile,
            "goals": _goal_context(user_id),
            "habits": _habit_context(user_id),
            "habit_trends": _compact_habit_trends(user_id),
            "current_state": get_current_state(user_id),
            "statistics": get_user_statistics(user_id),
            "checkin_trends": get_checkin_trends_context(user_id, limit=14),
            "memories": get_memories_context(user_id, limit=8),
            "conversation": get_conversation_context(user_id, limit=8),
        }

    return {
        "profile": {},
        "goals": [],
        "habits": [],
        "habit_trends": {},
        "current_state": {},
        "statistics": {},
        "memories": [],
        "conversation": [],
    }


def get_dan_context(user_id, context_level="basic"):
    """
    Совместимость со старым API.
    """
    level = "conversation" if context_level == "basic" else context_level
    return get_context_for_level(user_id, level)
