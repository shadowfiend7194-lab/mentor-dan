from datetime import datetime

from database.connection import get_connection


# =========================================================
# СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def create_user(
    user_id,
    name=None,
    age=None
):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (
            user_id,
            name,
            age,
            created_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            age,
            now
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ПОЛУЧИТЬ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def get_user(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            user_id,
            name,
            age,
            created_at,
            wake_time,
            sleep_time,
            last_morning_checkin,
            last_evening_checkin,
            morning_notifications_enabled,
            evening_notifications_enabled

        FROM users

        WHERE user_id = ?
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

        "user_id": row[0],

        "name": row[1],

        "age": row[2],

        "created_at": row[3],

        "wake_time": row[4],

        "sleep_time": row[5],

        "last_morning_checkin": row[6],

        "last_evening_checkin": row[7],

        "morning_notifications_enabled": (
            True
            if row[8] is None
            else bool(row[8])
        ),

        "evening_notifications_enabled": (
            True
            if row[9] is None
            else bool(row[9])
        )
    }



# =========================================================
# ОБНОВИТЬ РЕЖИМ ДНЯ
# =========================================================

def update_sleep_settings(
    user_id,
    wake_time=None,
    sleep_time=None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users

        SET
            wake_time = COALESCE(?, wake_time),
            sleep_time = COALESCE(?, sleep_time)

        WHERE user_id = ?
        """,
        (
            wake_time,
            sleep_time,
            user_id
        )
    )

    conn.commit()
    conn.close()



# =========================================================
# НАСТРОЙКИ УВЕДОМЛЕНИЙ
# =========================================================

def update_notification_settings(
    user_id,
    morning_enabled=None,
    evening_enabled=None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users

        SET

        morning_notifications_enabled =
        COALESCE(?, morning_notifications_enabled),

        evening_notifications_enabled =
        COALESCE(?, evening_notifications_enabled)

        WHERE user_id = ?

        """,
        (
            None if morning_enabled is None else int(morning_enabled),

            None if evening_enabled is None else int(evening_enabled),

            user_id
        )
    )

    conn.commit()
    conn.close()



# =========================================================
# ПРОВЕРКА ЧЕК-ИНА
# =========================================================

def can_do_checkin(
    user_id,
    checkin_type
):

    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    field = (
        "last_morning_checkin"
        if checkin_type == "morning"
        else
        "last_evening_checkin"
    )


    cursor.execute(
        f"""
        SELECT {field}

        FROM users

        WHERE user_id = ?

        """,
        (
            user_id,
        )
    )


    result = cursor.fetchone()

    conn.close()


    if not result:
        return True


    return result[0] != today



# =========================================================
# СОХРАНИТЬ ДАТУ ЧЕК-ИНА
# =========================================================

def update_checkin_date(
    user_id,
    checkin_type
):

    conn = get_connection()
    cursor = conn.cursor()


    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    field = (
        "last_morning_checkin"
        if checkin_type == "morning"
        else
        "last_evening_checkin"
    )


    cursor.execute(
        f"""
        UPDATE users

        SET {field} = ?

        WHERE user_id = ?

        """,
        (
            today,
            user_id
        )
    )


    conn.commit()
    conn.close()



# =========================================================
# СБРОС ОТПРАВКИ УВЕДОМЛЕНИЯ
# =========================================================

def reset_notification_sent(
    user_id,
    notification_type
):

    conn = get_connection()
    cursor = conn.cursor()


    field = (
        "morning_notification_sent"
        if notification_type == "morning"
        else
        "evening_notification_sent"
    )


    cursor.execute(
        f"""
        UPDATE users

        SET {field} = NULL

        WHERE user_id = ?

        """,
        (
            user_id,
        )
    )


    conn.commit()
    conn.close()



# =========================================================
# ОБНОВИТЬ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def update_user(
    user_id,
    name=None,
    age=None
):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE users

        SET
            name = COALESCE(?, name),
            age = COALESCE(?, age)

        WHERE user_id = ?

        """,
        (
            name,
            age,
            user_id
        )
    )


    conn.commit()
    conn.close()



# =========================================================
# СУЩЕСТВУЕТ ЛИ ПОЛЬЗОВАТЕЛЬ
# =========================================================

def user_exists(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT 1

        FROM users

        WHERE user_id = ?

        """,
        (
            user_id,
        )
    )


    result = cursor.fetchone()

    conn.close()


    return result is not None

# =========================================================
# ПОЛНОЕ УДАЛЕНИЕ ДАННЫХ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def delete_user_data(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # -------------------------------------------------
        # HABIT LOGS
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM habit_logs

            WHERE habit_id IN (
                SELECT id
                FROM habits
                WHERE user_id = ?
            )
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # HABITS
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM habits

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # CHECKINS
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM checkins

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # CHECK-IN HISTORY
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM checkin_history

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # GOALS
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM goals

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # WEEKLY REPORTS
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM weekly_reports

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # ДЭН — ИСТОРИЯ ПЕРЕПИСКИ
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM dan_messages

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # ДЭН — ДОЛГОСРОЧНАЯ ПАМЯТЬ
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM dan_memory

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        # -------------------------------------------------
        # ПОЛЬЗОВАТЕЛЬ
        # -------------------------------------------------
        cursor.execute(
            """
            DELETE FROM users

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()