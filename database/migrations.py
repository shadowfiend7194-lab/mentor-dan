from database.connection import get_connection


# =========================================================
# ДОБАВЛЕНИЕ СТОЛБЦА
# =========================================================

def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_type,
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if column_name not in columns:

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
            """
        )

        print(
            f"✅ Migration: "
            f"{table_name}.{column_name} added"
        )


# =========================================================
# МИГРАЦИЯ
# =========================================================

def migrate():

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # USERS
    # =====================================================

    add_column_if_missing(
        cursor,
        "users",
        "weekly_report_sent",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "wake_time",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "sleep_time",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "last_morning_checkin",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "last_evening_checkin",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "morning_notification_sent",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "evening_notification_sent",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "morning_notifications_enabled",
        "INTEGER DEFAULT 1"
    )

    add_column_if_missing(
        cursor,
        "users",
        "evening_notifications_enabled",
        "INTEGER DEFAULT 1"
    )

    # =====================================================
    # HABITS
    # =====================================================

    add_column_if_missing(
        cursor,
        "habits",
        "formed",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "formed_at",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "last_review_date",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "controlled",
        "INTEGER DEFAULT 0"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "controlled_at",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "difficulty",
        "INTEGER"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "motivation",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "goal_id",
        "INTEGER"
    )

    add_column_if_missing(
        cursor,
        "habits",
        "pro_status",
        "TEXT DEFAULT 'active'"
    )

    # =====================================================
    # GOALS
    # =====================================================

    add_column_if_missing(
        cursor,
        "goals",
        "status",
        "TEXT DEFAULT 'active'"
    )

    add_column_if_missing(
        cursor,
        "goals",
        "achieved_at",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "goals",
        "achievement_note",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "goals",
        "last_review_date",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "goals",
        "pro_status",
        "TEXT DEFAULT 'active'"
    )

    # =====================================================
    # CHECKINS
    # =====================================================

    add_column_if_missing(
        cursor,
        "checkins",
        "evening_problem",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "checkins",
        "evening_positive",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "checkins",
        "evening_improve",
        "TEXT"
    )

    # =====================================================
    # SUBSCRIPTIONS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL UNIQUE,

            plan TEXT NOT NULL DEFAULT 'pro',

            status TEXT NOT NULL DEFAULT 'active',

            started_at TEXT,

            expires_at TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            pro_setup_completed INTEGER DEFAULT 0

        )
        """
    )

    add_column_if_missing(
        cursor,
        "subscriptions",
        "pro_setup_completed",
        "INTEGER DEFAULT 0"
    )

    # =====================================================
    # ИНДЕКСЫ
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_habits_goal_id
        ON habits(goal_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_habits_user_goal
        ON habits(user_id, goal_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_subscriptions_user
        ON subscriptions(user_id)
        """
    )

    conn.commit()
    conn.close()

    print("✅ Migration complete")