from datetime import datetime, date, timedelta

from database.connection import get_connection


# =========================================================
# ЛИМИТЫ ПРИВЫЧЕК
# =========================================================

FREE_MAX_GOOD_HABITS = 1
FREE_MAX_BAD_HABITS = 1
PRO_MAX_GOOD_HABITS = 3
PRO_MAX_BAD_HABITS = 3


# =========================================================
# ДНИ НЕДЕЛИ
# =========================================================

DAY_NAMES = {
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс",
}


# =========================================================
# ПАРСИНГ СВОИХ ДНЕЙ
# =========================================================

def parse_custom_days(text):

    if not text:
        return None

    text = (
        text.lower()
        .replace("ё", "е")
        .replace(".", "")
        .strip()
    )

    mapping = {
        "пн": 0,
        "пон": 0,
        "понедельник": 0,

        "вт": 1,
        "вто": 1,
        "вторник": 1,

        "ср": 2,
        "среда": 2,

        "чт": 3,
        "чет": 3,
        "четверг": 3,

        "пт": 4,
        "пятница": 4,

        "сб": 5,
        "суббота": 5,

        "вс": 6,
        "воскресенье": 6,
    }

    result = []

    for item in text.split(","):

        item = item.strip()

        if item in mapping:
            result.append(
                mapping[item]
            )

    if not result:
        return None

    return sorted(
        set(result)
    )


# =========================================================
# ФОРМАТИРОВАНИЕ ДНЕЙ
# =========================================================

def format_custom_days(schedule_days):

    if not schedule_days:
        return "Не указано"

    try:

        days = [
            int(x)
            for x in str(schedule_days).split(",")
        ]

    except Exception:

        return "Не указано"

    return ", ".join(
        DAY_NAMES[d]
        for d in days
        if d in DAY_NAMES
    )


# =========================================================
# ФОРМАТИРОВАНИЕ ЧАСТОТЫ
# =========================================================

def format_frequency(
    frequency,
    schedule_days=None
):

    if frequency == "daily":
        return "Каждый день"

    if frequency == "weekdays":
        return "Понедельник–пятница"

    if frequency == "custom":

        return format_custom_days(
            schedule_days
        )

    return "Не указано"


# =========================================================
# СОЗДАНИЕ ПРИВЫЧКИ
# =========================================================

def create_habit(
    user_id,
    name,
    habit_type,
    frequency="daily",
    schedule_days=None,
    difficulty=None,
    motivation=None
):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if frequency == "custom":

        parsed = parse_custom_days(
            schedule_days
        )

        schedule_days = (
            ",".join(
                map(str, parsed)
            )
            if parsed
            else None
        )

    cursor.execute(
        """
        INSERT INTO habits
        (
            user_id,
            name,
            habit_type,
            frequency,
            schedule_days,
            difficulty,
            motivation,
            active,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)

        """,
        (
            user_id,
            name,
            habit_type,
            frequency,
            schedule_days,
            difficulty,
            motivation,
            now,
        )
    )

    habit_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return habit_id


# =========================================================
# ПОЛУЧЕНИЕ ПРИВЫЧЕК
# =========================================================

def get_user_habits(
    user_id
):

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
            goal_id,
            pro_status

        FROM habits

        WHERE user_id = ?

        AND active = 1

        ORDER BY id ASC

        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    habits = []

    for row in rows:

        habits.append(
            {
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
                "pro_status": row[14],
            }
        )

    return habits


def get_user_habits_for_plan(
    user_id,
    include_frozen=False,
):
    """
    Возвращает привычки с учётом состояния PRO.

    include_frozen=False — только доступные привычки.
    include_frozen=True — все активные привычки, включая замороженные.
    """

    habits = get_user_habits(user_id)

    if include_frozen:
        return habits

    return [
        habit
        for habit in habits
        if habit.get("pro_status") != "frozen"
    ]


# =========================================================
# МОЖНО ЛИ ВЫПОЛНЯТЬ ПРИВЫЧКУ В ЭТУ ДАТУ
# =========================================================

def is_habit_scheduled_on_date(
    habit,
    check_date=None
):

    if check_date is None:
        check_date = date.today()

    weekday = check_date.weekday()

    frequency = habit.get(
        "frequency"
    )

    if frequency == "daily":
        return True

    if frequency == "weekdays":
        return weekday < 5

    if frequency == "custom":

        days = habit.get(
            "schedule_days"
        )

        if not days:
            return False

        try:

            selected = {
                int(x)
                for x in str(days).split(",")
            }

        except Exception:

            return False

        return weekday in selected

    return False


# =========================================================
# СОВМЕСТИМОСТЬ СО СТАРЫМ КОДОМ
# =========================================================

def is_habit_scheduled_today(
    habit,
    check_date=None
):

    return is_habit_scheduled_on_date(
        habit,
        check_date
    )


# =========================================================
# ВЫПОЛНЕНИЕ
# =========================================================

def complete_habit(
    habit_id,
    completed=True
):

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute(
        """
        INSERT INTO habit_logs
        (
            habit_id,
            date,
            completed
        )

        VALUES (?, ?, ?)

        ON CONFLICT(habit_id,date)

        DO UPDATE SET

        completed = excluded.completed

        """,
        (
            habit_id,
            today,
            1 if completed else 0,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ВЫПОЛНЕНА ЛИ СЕГОДНЯ
# =========================================================

def is_completed_today(
    habit_id
):

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute(
        """
        SELECT completed

        FROM habit_logs

        WHERE habit_id = ?

        AND date = ?

        """,
        (
            habit_id,
            today,
        )
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    return bool(
        row[0]
    )


# =========================================================
# СЕРИЯ
# =========================================================

def get_habit_streak(
    habit_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date

        FROM habit_logs

        WHERE habit_id = ?

        AND completed = 1

        ORDER BY date DESC

        """,
        (
            habit_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return 0

    completed_dates = {
        datetime.strptime(
            row[0],
            "%Y-%m-%d"
        ).date()
        for row in rows
    }

    streak = 0

    current = date.today()

    while current in completed_dates:

        streak += 1

        current -= timedelta(
            days=1
        )

    return streak


# =========================================================
# СКОЛЬКО МОЖНО ВЫПОЛНИТЬ ЗА НЕДЕЛЮ
# =========================================================

def get_habit_week_target(
    user_id
):

    habits = get_user_habits(
        user_id
    )

    total = 0

    today = date.today()

    for i in range(7):

        current_day = (
            today -
            timedelta(days=i)
        )

        for habit in habits:

            if is_habit_scheduled_on_date(
                habit,
                current_day
            ):

                total += 1

    return total


# =========================================================
# ПОЛУЧИТЬ ПРИВЫЧКУ
# =========================================================

def get_habit(
    user_id,
    habit_id
):

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
            goal_id,
            pro_status

        FROM habits

        WHERE id = ?

        AND user_id = ?

        AND active = 1

        LIMIT 1

        """,
        (
            habit_id,
            user_id,
        )
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
        "pro_status": row[14],
    }


# =========================================================
# ОТМЕТИТЬ ПРОВЕРКУ ПРИВЫЧКИ
# =========================================================

def mark_habit_reviewed(
    user_id,
    habit_id,
    review_date
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET last_review_date = ?

        WHERE id = ?

        AND user_id = ?

        AND active = 1

        """,
        (
            review_date,
            habit_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# СФОРМИРОВАТЬ ПРИВЫЧКУ
# =========================================================

def mark_habit_formed(
    user_id,
    habit_id
):

    conn = get_connection()
    cursor = conn.cursor()

    formed_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        UPDATE habits

        SET
            formed = 1,
            formed_at = ?

        WHERE id = ?

        AND user_id = ?

        AND active = 1

        """,
        (
            formed_at,
            habit_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ДЕРЖАТЬ ПЛОХУЮ ПРИВЫЧКУ ПОД КОНТРОЛЕМ
# =========================================================

def mark_habit_controlled(
    user_id,
    habit_id
):

    conn = get_connection()
    cursor = conn.cursor()

    controlled_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        UPDATE habits

        SET
            controlled = 1,
            controlled_at = ?

        WHERE id = ?

        AND user_id = ?

        AND active = 1

        """,
        (
            controlled_at,
            habit_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# УДАЛЕНИЕ ПРИВЫЧКИ
# =========================================================

def mark_habit_removed(
    user_id,
    habit_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET active = 0

        WHERE id = ?

        AND user_id = ?

        """,
        (
            habit_id,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ПОЛУЧИТЬ ЛОГИ ПРИВЫЧКИ ЗА ПЕРИОД
# =========================================================

def get_habit_logs(
    habit_id,
    start_date,
    end_date
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

        ORDER BY date ASC

        """,
        (
            habit_id,
            start_date.isoformat(),
            end_date.isoformat(),
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "date": row[0],
            "completed": bool(row[1]),
        }
        for row in rows
    ]


# =========================================================
# СТАТИСТИКА ОДНОЙ ПРИВЫЧКИ
# =========================================================

def get_habit_completion_stats(
    habit,
    start_date,
    end_date
):

    logs = get_habit_logs(
        habit["id"],
        start_date,
        end_date,
    )

    logs_by_date = {
        item["date"]: item["completed"]
        for item in logs
    }

    scheduled = 0
    completed = 0

    current = start_date

    while current <= end_date:

        if is_habit_scheduled_on_date(
            habit,
            current
        ):

            scheduled += 1

            if logs_by_date.get(
                current.isoformat(),
                False
            ):

                completed += 1

        current += timedelta(
            days=1
        )

    percentage = (
        round(
            completed /
            scheduled *
            100
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
# СТАБИЛЬНОСТЬ ПРИВЫЧКИ
# =========================================================

def get_habit_stability(
    habit,
    days=14
):

    if days < 1:
        days = 1

    today = date.today()

    start_date = (
        today -
        timedelta(days=days - 1)
    )

    stats = get_habit_completion_stats(
        habit,
        start_date,
        today,
    )

    return {
        "habit_id": habit.get("id"),
        "habit_name": habit.get("name"),
        "scheduled": stats["scheduled"],
        "completed": stats["completed"],
        "stability": stats["percentage"],
        "period_days": days,
    }


# =========================================================
# СТАБИЛЬНОСТЬ ВСЕХ ПРИВЫЧЕК
# =========================================================

def get_user_habit_stability(
    user_id,
    days=14
):

    habits = get_user_habits(
        user_id
    )

    result = []

    for habit in habits:

        result.append(
            get_habit_stability(
                habit,
                days=days,
            )
        )

    return result