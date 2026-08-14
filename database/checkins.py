from datetime import date

from database.connection import get_connection


# =========================================================
# СОХРАНЕНИЕ ЧЕК-ИНА
# =========================================================

def save_checkin(
    user_id,

    morning_energy=None,
    morning_sleep=None,
    morning_mood=None,
    morning_stress=None,

    evening_score=None,
    evening_problem=None,
    evening_positive=None,
    evening_improve=None,
):

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()


    cursor.execute(
        """
        SELECT id
        FROM checkins
        WHERE user_id = ?
        AND date = ?
        """,
        (
            user_id,
            today,
        )
    )

    row = cursor.fetchone()


    # -----------------------------------------------------
    # ЗАПИСЬ УЖЕ ЕСТЬ
    # -----------------------------------------------------

    if row:

        checkin_id = row[0]


        cursor.execute(
            """
            UPDATE checkins

            SET

                morning_energy = COALESCE(?, morning_energy),
                morning_sleep = COALESCE(?, morning_sleep),
                morning_mood = COALESCE(?, morning_mood),
                morning_stress = COALESCE(?, morning_stress),

                evening_score = COALESCE(?, evening_score),
                evening_problem = COALESCE(?, evening_problem),
                evening_positive = COALESCE(?, evening_positive),
                evening_improve = COALESCE(?, evening_improve)

            WHERE id = ?

            """,
            (
                morning_energy,
                morning_sleep,
                morning_mood,
                morning_stress,

                evening_score,
                evening_problem,
                evening_positive,
                evening_improve,

                checkin_id,
            )
        )


    # -----------------------------------------------------
    # НОВАЯ ЗАПИСЬ
    # -----------------------------------------------------

    else:

        cursor.execute(
            """
            INSERT INTO checkins
            (
                user_id,
                date,

                morning_energy,
                morning_sleep,
                morning_mood,
                morning_stress,

                evening_score,
                evening_problem,
                evening_positive,
                evening_improve
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """,
            (
                user_id,
                today,

                morning_energy,
                morning_sleep,
                morning_mood,
                morning_stress,

                evening_score,
                evening_problem,
                evening_positive,
                evening_improve,
            )
        )


    conn.commit()
    conn.close()



# =========================================================
# ПОСЛЕДНИЕ ЧЕК-ИНЫ
# =========================================================

def get_recent_checkins(
    user_id,
    limit=7,
):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

            date,

            morning_energy,
            morning_sleep,
            morning_mood,
            morning_stress,

            evening_score,
            evening_problem,
            evening_positive,
            evening_improve

        FROM checkins

        WHERE user_id = ?

        ORDER BY date DESC

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



# =========================================================
# ЧЕК-ИН ЗА СЕГОДНЯ
# =========================================================

def get_today_checkin(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()


    cursor.execute(
        """
        SELECT

            date,

            morning_energy,
            morning_sleep,
            morning_mood,
            morning_stress,

            evening_score,
            evening_problem,
            evening_positive,
            evening_improve

        FROM checkins

        WHERE user_id = ?

        AND date = ?

        """,
        (
            user_id,
            today,
        )
    )


    row = cursor.fetchone()

    conn.close()

    return row