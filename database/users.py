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
            last_evening_checkin

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
    }


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
# ПРОВЕРКА СУЩЕСТВОВАНИЯ
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