from database.connection import get_connection


# =========================================================
# ДОБАВЛЕНИЕ СТОЛБЦА ЕСЛИ НЕТ
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

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if column_name not in columns:

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
            """
        )


# =========================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ
# =========================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()


    # =====================================================
    # USERS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY,

            name TEXT,

            age TEXT,

            created_at TEXT

        )
        """
    )

    add_column_if_missing(
        cursor,
        "users",
        "weekly_report_sent",
        "TEXT"
    )

    # =====================================================
    # HABITS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            habit_type TEXT NOT NULL,

            frequency TEXT DEFAULT 'daily',

            schedule_days TEXT,

            active INTEGER DEFAULT 1,

            created_at TEXT

        )
        """
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
    # CHECKINS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS checkins (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            date TEXT NOT NULL,

            morning_energy INTEGER,

            morning_sleep INTEGER,

            morning_mood INTEGER,

            morning_stress INTEGER,

            evening_score INTEGER

        )
        """
    )


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
    # GOALS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            is_main INTEGER DEFAULT 0,

            active INTEGER DEFAULT 1,

            created_at TEXT

        )
        """
    )
    

    cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS checkin_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            type TEXT NOT NULL,

            date TEXT NOT NULL,

            completed INTEGER DEFAULT 0

        )
        """
    )

   

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS weekly_reports (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        report_date TEXT NOT NULL,

        text TEXT NOT NULL

    )
    """
    )

    conn.commit()
    conn.close()


    print("✅ Database initialized")