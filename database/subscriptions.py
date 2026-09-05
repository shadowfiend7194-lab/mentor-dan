from datetime import datetime, timedelta

from database.connection import get_connection


# =========================================================
# ВНУТРЕННИЕ ДАТЫ
# =========================================================

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _now():
    return datetime.now()


def _now_string():
    return _now().strftime(
        DATE_FORMAT
    )


def _parse_datetime(value):

    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.strptime(
            str(value),
            DATE_FORMAT
        )
    except (
        ValueError,
        TypeError
    ):
        return None


# =========================================================
# ПОЛУЧИТЬ ПОДПИСКУ
# =========================================================

def get_subscription(
    user_id
):

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
            updated_at,
            pro_setup_completed
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

        "pro_setup_completed": bool(
            row[8]
        ),

    }

    # =====================================================
    # АВТОМАТИЧЕСКОЕ ИСТЕЧЕНИЕ
    # =====================================================

    if (
        subscription["plan"] == "pro"
        and subscription["status"] == "active"
        and subscription["expires_at"]
    ):

        expires_at = _parse_datetime(
            subscription["expires_at"]
        )

        if (
            expires_at
            and expires_at <= _now()
        ):

            now = _now_string()

            cursor.execute(
                """
                UPDATE subscriptions

                SET
                    status = 'expired',
                    updated_at = ?

                WHERE user_id = ?

                AND plan = 'pro'

                AND status = 'active'
                """,
                (
                    now,
                    user_id,
                )
            )

            conn.commit()

            subscription["status"] = "expired"

            subscription["updated_at"] = now

    conn.close()

    return subscription


# =========================================================
# PRO АКТИВЕН?
# =========================================================

def is_pro(
    user_id
):

    subscription = get_subscription(
        user_id
    )

    if not subscription:
        return False

    if subscription["plan"] != "pro":
        return False

    if subscription["status"] != "active":
        return False

    expires_at = _parse_datetime(
        subscription["expires_at"]
    )

    if not expires_at:
        return False

    return expires_at > _now()


# =========================================================
# SETUP УЖЕ БЫЛ ПРОЙДЕН?
# =========================================================

def is_pro_setup_completed(
    user_id
):

    subscription = get_subscription(
        user_id
    )

    if not subscription:
        return False

    return bool(
        subscription.get(
            "pro_setup_completed"
        )
    )


# =========================================================
# ПОМЕТИТЬ SETUP ЗАВЕРШЁННЫМ
# =========================================================

def mark_pro_setup_completed(
    user_id
):

    now = _now_string()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE subscriptions

        SET
            pro_setup_completed = 1,
            updated_at = ?

        WHERE user_id = ?
        """,
        (
            now,
            user_id,
        )
    )

    conn.commit()

    changed = (
        cursor.rowcount > 0
    )

    conn.close()

    return changed


# =========================================================
# АКТИВАЦИЯ TEST PRO
# =========================================================

def activate_test_pro(
    user_id,
    days=30
):

    now = _now()

    started_at = now.strftime(
        DATE_FORMAT
    )

    expires_at = (
        now + timedelta(
            days=days
        )
    ).strftime(
        DATE_FORMAT
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            pro_setup_completed
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
                updated_at,
                pro_setup_completed
            )

            VALUES (
                ?,
                'pro',
                'active',
                ?,
                ?,
                ?,
                ?,
                0
            )
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

def expire_pro(
    user_id
):

    now = _now_string()

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

    changed = (
        cursor.rowcount > 0
    )

    conn.close()

    return changed


# =========================================================
# УДАЛИТЬ ПОДПИСКУ
# =========================================================

def delete_subscription(
    user_id
):

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

    changed = (
        cursor.rowcount > 0
    )

    conn.close()

    return changed