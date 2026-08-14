from datetime import date, timedelta

from database.connection import get_connection
from database.habits import (
    get_user_habits,
    get_habit_streak,
    is_habit_scheduled_today,
)


# =========================================================
# ЛУЧШАЯ СЕРИЯ
# =========================================================

def get_best_streak(
    user_id
):

    habits = get_user_habits(
        user_id
    )

    best = 0


    for habit in habits:

        streak = get_habit_streak(
            habit["id"]
        )

        if streak > best:
            best = streak


    return best



# =========================================================
# СКОЛЬКО ВЫПОЛНЕНИЙ ВОЗМОЖНО ЗА НЕДЕЛЮ
# =========================================================

def get_week_habit_target(
    user_id
):

    habits = get_user_habits(
        user_id
    )


    today = date.today()


    total = 0


    for i in range(7):

        current_day = (
            today - timedelta(days=i)
        )


        # временно считаем через дату
        # без записи логов

        for habit in habits:

            if is_habit_scheduled_today(
                habit,
                current_day
            ):
                total += 1


    return total



# =========================================================
# ВЫПОЛНЕНО ЗА НЕДЕЛЮ
# =========================================================

def get_week_habit_progress(
    user_id
):

    today = date.today()


    week_start = (
        today - timedelta(days=6)
    ).isoformat()


    today_str = today.isoformat()



    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT COUNT(*)

        FROM habit_logs hl

        JOIN habits h

        ON h.id = hl.habit_id


        WHERE h.user_id = ?

        AND h.active = 1

        AND hl.completed = 1

        AND hl.date BETWEEN ? AND ?

        """,

        (
            user_id,
            week_start,
            today_str
        )
    )


    completed = cursor.fetchone()[0]


    conn.close()



    total = get_week_habit_target(
        user_id
    )


    return {

        "completed": completed,

        "total": total

    }



# =========================================================
# СРЕДНИЕ УТРЕННИЕ ЗНАЧЕНИЯ
# =========================================================

def get_morning_averages(
    user_id
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        AVG(morning_energy),
        AVG(morning_sleep),
        AVG(morning_mood),
        AVG(morning_stress)


        FROM checkins


        WHERE user_id = ?

        """,

        (
            user_id,
        )
    )


    row = cursor.fetchone()


    conn.close()



    return {

        "energy":
            round(row[0],1)
            if row[0]
            else 0,


        "sleep":
            round(row[1],1)
            if row[1]
            else 0,


        "mood":
            round(row[2],1)
            if row[2]
            else 0,


        "stress":
            round(row[3],1)
            if row[3]
            else 0,

    }



# =========================================================
# ВЕЧЕРНЯЯ ОЦЕНКА
# =========================================================

def get_evening_average(
    user_id
):

    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT AVG(evening_score)

        FROM checkins

        WHERE user_id = ?

        AND evening_score IS NOT NULL

        """,

        (
            user_id,
        )
    )



    row = cursor.fetchone()


    conn.close()



    if not row or row[0] is None:

        return 0



    return round(
        row[0],
        1
    )



# =========================================================
# ОБЩАЯ СТАТИСТИКА
# =========================================================

def get_progress_summary(
    user_id
):


    streak = get_best_streak(
        user_id
    )


    week = get_week_habit_progress(
        user_id
    )


    morning = get_morning_averages(
        user_id
    )


    evening = get_evening_average(
        user_id)



    return {


        "best_streak":
            streak,


        "week_completed":
            week["completed"],


        "week_total":
            week["total"],



        "energy":
            morning["energy"],


        "sleep":
            morning["sleep"],


        "mood":
            morning["mood"],


        "stress":
            morning["stress"],



        "evening_score":
            evening,

    }