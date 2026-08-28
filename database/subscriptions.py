from datetime import datetime, timedelta

from database.connection import get_connection


# =========================================================
# ПОЛУЧИТЬ ПОДПИСКУ
# =========================================================

def get_subscription(user_id):
    """
    Возвращает текущую подписку пользователя.

    Если подписки нет:
        None

    Если Pro активен:
        status = "active"

    Если Pro закончился:
        status = "expired"
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            plan,
            status,
            started_at,
            expires_at,
            created_at,
            updated_at
        FROM subscriptions
        WHERE user_id = ?
        LIMIT 1
        """,
        (
            user_id,
        )
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    subscription = {
        "id": row[0],
        "user_id": row[1],
        "plan": row[2],
        "status": row[3],
        "started_at": row[4],
        "expires_at": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }

    # -----------------------------------------------------
    # АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ИСТЁКШЕГО PRO
    # -----------------------------------------------------

    if (
        subscription["plan"] == "pro"
        and subscription["status"] == "active"
        and subscription["expires_at"]
    ):

        try:

            expires_at = datetime.strptime(
                subscription["expires_at"],
                "%Y-%m-%d %H:%M:%S"
            )

            if expires_at <= datetime.now():

                now = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                cursor.execute(
                    """
                    UPDATE subscriptions

                    SET
                        status = 'expired',
                        updated_at = ?

                    WHERE user_id = ?
                    """,
                    (
                        now,
                        user_id,
                    )
                )

                conn.commit()

                subscription["status"] = "expired"
                subscription["updated_at"] = now

        except ValueError:
            pass

    conn.close()

    return subscription


# =========================================================
# АКТИВЕН ЛИ PRO
# =========================================================

def is_pro(user_id):
    """
    Возвращает True только если Pro реально активен
    и срок подписки ещё не закончился.
    """

    subscription = get_subscription(
        user_id
    )

    if not subscription:
        return False

    if subscription["plan"] != "pro":
        return False

    if subscription["status"] != "active":
        return False

    if not subscription["expires_at"]:
        return False

    try:

        expires_at = datetime.strptime(
            subscription["expires_at"],
            "%Y-%m-%d %H:%M:%S"
        )

    except ValueError:

        return False

    return expires_at > datetime.now()


# =========================================================
# АКТИВИРОВАТЬ TEST PRO
# =========================================================

def activate_test_pro(
    user_id,
    days=30
):
    """
    Тестовая активация Pro.

    Используется только на этапе разработки.
    Оплаты здесь нет.
    """

    now = datetime.now()

    started_at = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    expires_at = (
        now + timedelta(days=days)
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM subscriptions
        WHERE user_id = ?
        LIMIT 1
        """,
        (
            user_id,
        )
    )

    existing = cursor.fetchone()

    if existing:

        cursor.execute(
            """
            UPDATE subscriptions

            SET
                plan = 'pro',
                status = 'active',
                started_at = ?,
                expires_at = ?,
                updated_at = ?

            WHERE user_id = ?
            """,
            (
                started_at,
                expires_at,
                started_at,
                user_id,
            )
        )

    else:

        cursor.execute(
            """
            INSERT INTO subscriptions
            (
                user_id,
                plan,
                status,
                started_at,
                expires_at,
                created_at,
                updated_at
            )

            VALUES (?, 'pro', 'active', ?, ?, ?, ?)
            """,
            (
                user_id,
                started_at,
                expires_at,
                started_at,
                started_at,
            )
        )

    conn.commit()
    conn.close()

    return get_subscription(
        user_id
    )


# =========================================================
# ПРИНУДИТЕЛЬНО ЗАВЕРШИТЬ PRO
# =========================================================

def expire_pro(user_id):
    """
    Принудительно переводит Pro в expired.

    Ничего не удаляет.
    """

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE subscriptions

        SET
            status = 'expired',
            expires_at = ?,
            updated_at = ?

        WHERE user_id = ?
        AND plan = 'pro'
        """,
        (
            now,
            now,
            user_id,
        )
    )

    conn.commit()

    changed = cursor.rowcount

    conn.close()

    return changed > 0


# =========================================================
# УДАЛИТЬ ПОДПИСКУ
# =========================================================

def delete_subscription(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM subscriptions

        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    conn.commit()
    conn.close()