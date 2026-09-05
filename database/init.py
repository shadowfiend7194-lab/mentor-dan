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

            created_at TEXT,

            weekly_report_sent TEXT,

            wake_time TEXT,

            sleep_time TEXT,

            last_morning_checkin TEXT,

            last_evening_checkin TEXT,

            morning_notification_sent TEXT,

            evening_notification_sent TEXT,

            morning_notifications_enabled INTEGER DEFAULT 1,

            evening_notifications_enabled INTEGER DEFAULT 1

        )
        """
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

            created_at TEXT,

            formed INTEGER DEFAULT 0,

            formed_at TEXT,

            last_review_date TEXT,

            controlled INTEGER DEFAULT 0,

            controlled_at TEXT,

            difficulty INTEGER,

            motivation TEXT,

            goal_id INTEGER,

            pro_status TEXT DEFAULT 'active'

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

            evening_score INTEGER,

            evening_problem TEXT,

            evening_positive TEXT,

            evening_improve TEXT

        )
        """
    )

    # =====================================================
    # CHECK-IN HISTORY
    # =====================================================

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

            created_at TEXT,

            status TEXT DEFAULT 'active',

            achieved_at TEXT,

            achievement_note TEXT,

            last_review_date TEXT,

            pro_status TEXT DEFAULT 'active'

        )
        """
    )

    # =====================================================
    # WEEKLY REPORTS
    # =====================================================

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

    # =====================================================
    # EVENTS
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
    # ACHIEVEMENTS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_achievements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            achievement_key TEXT NOT NULL,

            earned_at TEXT NOT NULL,

            UNIQUE(
                user_id,
                achievement_key
            )

        )
        """
    )

    # =====================================================
    # DAN — ИСТОРИЯ
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
    # DAN — ДОЛГОСРОЧНАЯ ПАМЯТЬ
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
    # SUBSCRIPTIONS
    # =====================================================
    #
    # ЕДИНСТВЕННЫЙ источник истины для PRO.
    #
    # users.pro_active / users.pro_expires_at
    # больше не используются системой доступа.
    #
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

    # =====================================================
    # ДОПОЛНИТЕЛЬНЫЕ КОЛОНКИ
    # =====================================================
    #
    # Нужны для старых БД, которые были созданы
    # предыдущими версиями проекта.
    #
    # =====================================================

    # USERS

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

    # HABITS

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

    # GOALS

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

    # CHECKINS

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

    # SUBSCRIPTIONS

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
        idx_habits_user
        ON habits(user_id)
        """
    )

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
        idx_habit_logs_habit_date
        ON habit_logs(habit_id, date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_checkins_user_date
        ON checkins(user_id, date)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_goals_user
        ON goals(user_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_subscriptions_user
        ON subscriptions(user_id)
        """
    )

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

    print("✅ Database initialized")