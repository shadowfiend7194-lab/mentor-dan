from datetime import datetime

from database.connection import get_connection


# =========================================================
# PRO — ПРОВЕРКА ПОДПИСКИ
# =========================================================

def is_user_pro(user_id):
    """
    Проверяет, активен ли PRO у пользователя.

    Пока используется только дата окончания.
    Платёжная система здесь НЕ реализуется.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pro_active,
            pro_expires_at
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    pro_active = bool(row[0])
    expires_at = row[1]

    if not pro_active:
        return False

    if not expires_at:
        return True

    try:
        expires = datetime.strptime(
            expires_at,
            "%Y-%m-%d %H:%M:%S"
        )

        return datetime.now() < expires

    except (ValueError, TypeError):

        return False


# =========================================================
# PRO — ПОЛУЧИТЬ СОСТОЯНИЕ
# =========================================================

def get_pro_status(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pro_active,
            pro_started_at,
            pro_expires_at
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if not row:

        return {
            "active": False,
            "started_at": None,
            "expires_at": None,
        }

    active = bool(row[0])

    if active and row[2]:

        try:

            expires = datetime.strptime(
                row[2],
                "%Y-%m-%d %H:%M:%S"
            )

            if datetime.now() >= expires:
                active = False

        except (ValueError, TypeError):

            pass

    return {
        "active": active,
        "started_at": row[1],
        "expires_at": row[2],
    }


# =========================================================
# PRO — АКТИВИРОВАТЬ
# =========================================================

def activate_pro(
    user_id,
    expires_at=None,
):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        UPDATE users

        SET
            pro_active = 1,
            pro_started_at = ?,
            pro_expires_at = ?

        WHERE user_id = ?
        """,
        (
            now,
            expires_at,
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# PRO — ОТКЛЮЧИТЬ
# =========================================================

def deactivate_pro(
    user_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users

        SET
            pro_active = 0

        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# PRO — ВКЛЮЧИТЬ РАСШИРЕННЫЙ РЕЖИМ ПРИВЫЧЕК
# =========================================================

def enable_pro_habits(
    user_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET
            pro_enabled = 1

        WHERE user_id = ?
        AND active = 1
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# PRO — ВКЛЮЧИТЬ РАСШИРЕННЫЙ РЕЖИМ ЦЕЛЕЙ
# =========================================================

def enable_pro_goals(
    user_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE goals

        SET
            pro_enabled = 1

        WHERE user_id = ?
        AND active = 1
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# PRO — ПОЛНЫЙ ПЕРЕХОД ПОЛЬЗОВАТЕЛЯ В PRO
# =========================================================

def enable_pro_features(
    user_id,
):

    enable_pro_habits(
        user_id
    )

    enable_pro_goals(
        user_id
    )


# =========================================================
# PRO — ВЫКЛЮЧИТЬ РАСШИРЕННЫЕ ФУНКЦИИ
# =========================================================

def disable_pro_features(
    user_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET
            pro_enabled = 0

        WHERE user_id = ?
        """,
        (user_id,)
    )

    cursor.execute(
        """
        UPDATE goals

        SET
            pro_enabled = 0

        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()