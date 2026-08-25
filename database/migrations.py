from database.connection import get_connection


# =========================================================
# МИГРАЦИИ
# =========================================================

def migrate():

    conn = get_connection()
    cursor = conn.cursor()


    # =====================================================
    # HABITS
    # =====================================================

    cursor.execute(
        """
        PRAGMA table_info(habits)
        """
    )

    habit_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    habit_fields = {


        "schedule_days":
        "TEXT",

        "formed":
        "INTEGER DEFAULT 0",

        "formed_at":
        "TEXT",

        "last_review_date":
        "TEXT",

        "controlled":
        "INTEGER DEFAULT 0",

        "controlled_at":
        "TEXT",
    }

    for field, field_type in habit_fields.items():

        if field not in habit_columns:

            cursor.execute(
                f"""
                ALTER TABLE habits
                ADD COLUMN {field} {field_type}
                """
            )

            print(
                f"✅ Added {field} to habits"
            )


    # =====================================================
    # HABIT LOGS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            habit_id INTEGER NOT NULL,

            date TEXT NOT NULL,

            completed INTEGER DEFAULT 0,

            UNIQUE(
                habit_id,
                date
            )

        )
        """
    )


    # =====================================================
    # GOALS
    # =====================================================

    cursor.execute(
        """
        PRAGMA table_info(goals)
        """
    )

    goal_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    goal_fields = {

        "status":
        "TEXT DEFAULT 'active'",

        "achieved_at":
        "TEXT",

        "achievement_note":
        "TEXT",

        "last_review_date":
        "TEXT",
    }


    for field, field_type in goal_fields.items():

        if field not in goal_columns:

            cursor.execute(
                f"""
                ALTER TABLE goals
                ADD COLUMN {field} {field_type}
                """
            )

            print(
                f"✅ Added {field} to goals"
            )


    # =====================================================
    # USERS
    # =====================================================

    user_fields = {

        "wake_time":
        "TEXT",

        "sleep_time":
        "TEXT",

        "last_morning_checkin":
        "TEXT",

        "last_evening_checkin":
        "TEXT",

        "morning_notification_sent":
        "TEXT",

        "evening_notification_sent":
        "TEXT",

        "morning_notifications_enabled":
        "INTEGER DEFAULT 1",

        "evening_notifications_enabled":
        "INTEGER DEFAULT 1",
    }


    cursor.execute(
        """
        PRAGMA table_info(users)
        """
    )

    user_columns = [
        row[1]
        for row in cursor.fetchall()
    ]


    for field, field_type in user_fields.items():

        if field not in user_columns:

            cursor.execute(
                f"""
                ALTER TABLE users
                ADD COLUMN {field} {field_type}
                """
            )

            print(
                f"✅ Added {field}"
            )


    # =====================================================
    # ИСТОРИЯ ПУТИ
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            event_type TEXT NOT NULL,

            title TEXT NOT NULL,

            description TEXT,

            created_at TEXT NOT NULL,

            UNIQUE(
                user_id,
                event_type
            )

        )
        """
    )


    # =====================================================
    # DENA — ИСТОРИЯ ПЕРЕПИСКИ
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dan_messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            role TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
        """
    )


    # =====================================================
    # DENA — ДОЛГОСРОЧНАЯ ПАМЯТЬ
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dan_memory (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            memory_key TEXT NOT NULL,

            memory_value TEXT NOT NULL,

            importance INTEGER DEFAULT 5,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
        """
    )


    # =====================================================
    # ИНДЕКСЫ DENA
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_dan_messages_user
        ON dan_messages(user_id)
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_dan_messages_user_date
        ON dan_messages(user_id, created_at)
        """
    )


    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_dan_memory_user
        ON dan_memory(user_id)
        """
    )


    conn.commit()
    conn.close()


    print(
        "✅ Migration complete"
    )