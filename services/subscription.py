from database.subscriptions import (
    get_subscription,
    is_pro,
    activate_test_pro,
    expire_pro,
    is_pro_setup_completed,
    mark_pro_setup_completed,
)


# =========================================================
# ВОССТАНОВЛЕНИЕ PRO-ДАННЫХ
# =========================================================

def _restore_pro_items(user_id):
    """Размораживает все активные PRO-элементы пользователя."""
    from database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET pro_status = 'active'
        WHERE user_id = ?
          AND active = 1
          AND pro_status = 'frozen'
        """,
        (user_id,),
    )
    habits_restored = cursor.rowcount

    cursor.execute(
        """
        UPDATE goals
        SET pro_status = 'active'
        WHERE user_id = ?
          AND active = 1
          AND pro_status = 'frozen'
        """,
        (user_id,),
    )
    goals_restored = cursor.rowcount

    conn.commit()
    conn.close()

    return habits_restored, goals_restored


def has_frozen_pro_data(user_id):
    """
    Проверяет, есть ли у пользователя сохранённые PRO-данные.

    Важно: ищем только active=1 + pro_status=frozen.
    История, удалённые элементы и обычные FREE-элементы
    не считаются признаком возврата в PRO.
    """
    from database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM habits
        WHERE user_id = ?
          AND active = 1
          AND pro_status = 'frozen'
        LIMIT 1
        """,
        (user_id,),
    )
    has_frozen_habit = cursor.fetchone() is not None

    if has_frozen_habit:
        conn.close()
        return True

    cursor.execute(
        """
        SELECT 1
        FROM goals
        WHERE user_id = ?
          AND active = 1
          AND pro_status = 'frozen'
        LIMIT 1
        """,
        (user_id,),
    )
    has_frozen_goal = cursor.fetchone() is not None

    conn.close()
    return has_frozen_goal


# =========================================================
# ЗАМОРОЗКА PRO-ДАННЫХ ПОСЛЕ ОКОНЧАНИЯ
# =========================================================

def _sync_expired_pro_state(user_id):
    """
    Переводит пользователя из PRO в корректное FREE-состояние.

    FREE сохраняет:
      - одну good-привычку;
      - одну bad-привычку;
      - одну главную/первую цель.

    Остальные активные PRO-элементы становятся frozen.
    Никакие записи не удаляются.
    """
    from database.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, habit_type
        FROM habits
        WHERE user_id = ?
          AND active = 1
        ORDER BY id ASC
        """,
        (user_id,),
    )
    habits = cursor.fetchall()

    keep_habits = []

    for wanted_type in ("good", "bad"):
        for habit_id, habit_type in habits:
            if habit_type == wanted_type and habit_id not in keep_habits:
                keep_habits.append(habit_id)
                break

    # Если одного типа нет — сохраняем второй FREE-слот
    # за любым оставшимся активным элементом.
    for habit_id, _ in habits:
        if len(keep_habits) >= 2:
            break
        if habit_id not in keep_habits:
            keep_habits.append(habit_id)

    cursor.execute(
        """
        UPDATE habits
        SET pro_status = 'frozen'
        WHERE user_id = ?
          AND active = 1
        """,
        (user_id,),
    )

    for habit_id in keep_habits:
        cursor.execute(
            """
            UPDATE habits
            SET pro_status = 'active'
            WHERE id = ?
              AND user_id = ?
              AND active = 1
            """,
            (habit_id, user_id),
        )

    cursor.execute(
        """
        SELECT id
        FROM goals
        WHERE user_id = ?
          AND active = 1
        ORDER BY is_main DESC, id ASC
        """,
        (user_id,),
    )
    goals = [row[0] for row in cursor.fetchall()]
    main_goal = goals[0] if goals else None

    cursor.execute(
        """
        UPDATE goals
        SET pro_status = 'frozen'
        WHERE user_id = ?
          AND active = 1
        """,
        (user_id,),
    )

    if main_goal is not None:
        cursor.execute(
            """
            UPDATE goals
            SET pro_status = 'active'
            WHERE id = ?
              AND user_id = ?
              AND active = 1
            """,
            (main_goal, user_id),
        )

    conn.commit()
    conn.close()


# =========================================================
# ТЕКУЩИЙ ТАРИФ
# =========================================================

def get_user_plan(user_id):
    subscription = get_subscription(user_id)

    if subscription is None:
        return "free"

    if (
        subscription["plan"] == "pro"
        and subscription["status"] == "active"
        and is_pro(user_id)
    ):
        return "pro"

    if (
        subscription["plan"] == "pro"
        and subscription["status"] == "expired"
    ):
        _sync_expired_pro_state(user_id)
        return "pro_expired"

    return "free"


# =========================================================
# PRO?
# =========================================================

def user_has_pro(user_id):
    return is_pro(user_id)


def is_pro_user(user_id):
    """Совместимый alias для старого кода."""
    return is_pro(user_id)


# =========================================================
# SETUP
# =========================================================

def has_completed_pro_setup(user_id):
    return is_pro_setup_completed(user_id)


def complete_pro_setup(user_id):
    return mark_pro_setup_completed(user_id)


# =========================================================
# TEST PRO
# =========================================================

def enable_test_pro(user_id, days=30):
    """
    Единая точка тестовой активации PRO.

    Возвращает:
      - состояние setup до активации;
      - результат активации;
      - количество восстановленных frozen-элементов.

    Восстановление выполняется после активации, когда is_pro()
    уже начинает возвращать True.
    """
    setup_was_completed = has_completed_pro_setup(user_id)

    activation = activate_test_pro(
        user_id,
        days=days,
    )

    habits_restored, goals_restored = _restore_pro_items(user_id)

    return {
        "activation": activation,
        "was_setup_completed": setup_was_completed,
        "habits_restored": habits_restored,
        "goals_restored": goals_restored,
    }


def disable_test_pro(user_id):
    return expire_pro(user_id)
