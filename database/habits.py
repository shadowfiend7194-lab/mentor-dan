from datetime import datetime, date, timedelta

from database.connection import get_connection


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

    except:

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
            motivation

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
            }
        )

    return habits



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

        except:

            return False



        return weekday in selected



    return False



# совместимость со старым кодом

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

def get_habit_streak(habit_id):

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
        (habit_id,)
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

        current -= timedelta(days=1)

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
            last_review_date
        FROM habits
        WHERE id = ?
        AND user_id = ?
        AND active = 1
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
            user_id
        )
    )

    conn.commit()
    conn.close()

    
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