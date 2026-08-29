from database.connection import get_connection


# =========================================================
# МИГРАЦИЯ БАЗЫ ДАННЫХ
# =========================================================

def migrate():

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # HABITS
    # =====================================================
    #
    # Добавляем PRO-связь:
    #
    # habit -> goal
    #
    # goal_id хранит ID цели, к которой относится привычка.
    #
    # NULL означает:
    # - привычка не связана с целью;
    # - либо PRO ещё не настроен.
    #
    # =====================================================

    cursor.execute(
        "PRAGMA table_info(habits)"
    )

    habit_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if "goal_id" not in habit_columns:

        cursor.execute(
            """
            ALTER TABLE habits
            ADD COLUMN goal_id INTEGER
            """
        )

        print(
            "✅ Migration: habits.goal_id added"
        )

    # =====================================================
    # PRO STATUS
    # =====================================================
    #
    # ВАЖНО:
    #
    # Состояние PRO НЕ хранится внутри habits.
    #
    # Активность PRO определяется существующей
    # системой подписки.
    #
    # Поэтому отдельный pro_status в habits
    # НЕ добавляем.
    #
    # =====================================================

    # =====================================================
    # ИНДЕКС ДЛЯ СВЯЗЕЙ
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_habits_goal_id
        ON habits(goal_id)
        """
    )

    # =====================================================
    # ИНДЕКС ПОЛЬЗОВАТЕЛЯ И ЦЕЛИ
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_habits_user_goal
        ON habits(user_id, goal_id)
        """
    )

    conn.commit()
    conn.close()

    print(
        "✅ Migration complete"
    )

