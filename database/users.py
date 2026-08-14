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
            created_at

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

    }



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