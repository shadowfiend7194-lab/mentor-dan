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


    if "schedule_days" not in habit_columns:

        cursor.execute(
            """
            ALTER TABLE habits
            ADD COLUMN schedule_days TEXT
            """
        )

        print(
            "✅ Added schedule_days to habits"
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
    # USERS — РЕЖИМ ДНЯ
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


    conn.commit()
    conn.close()


    print(
        "✅ Migration complete"
    )