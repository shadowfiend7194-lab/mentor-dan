from database.connection import get_connection



# =========================================================
# МИГРАЦИИ
# =========================================================

def migrate():

    conn = get_connection()
    cursor = conn.cursor()


    # -----------------------------------------------------
    # HABITS
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # HABIT LOGS
    # -----------------------------------------------------

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

def migrate():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        PRAGMA table_info(habits)
        """
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "schedule_days" not in columns:

        cursor.execute(
            """
            ALTER TABLE habits
            ADD COLUMN schedule_days TEXT
            """
        )

        print("✅ Added schedule_days")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            habit_id INTEGER NOT NULL,

            date TEXT NOT NULL,

            completed INTEGER DEFAULT 0,

            UNIQUE(habit_id, date)

        )
        """
    )

    conn.commit()
    conn.close()

    print("✅ Migration complete")