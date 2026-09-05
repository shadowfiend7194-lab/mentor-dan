from database.connection import get_connection
from services.subscription import disable_test_pro


def reset_pro_for_test(user_id):
    """
    Тестовый переход PRO -> FREE.

    Ничего не удаляет и не обнуляет PRO-данные.
    Оставляет доступными первые две привычки (предпочтительно
    по одной полезной и нежелательной) и главную цель.
    Остальные активные PRO-элементы переводятся в frozen.
    """

    pro_disabled = disable_test_pro(user_id)

    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # ПРИВЫЧКИ
    # -----------------------------------------------------
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

    keep_ids = []

    # Сохраняем одну good и одну bad, если они есть.
    for wanted_type in ("good", "bad"):
        for habit_id, habit_type in habits:
            if habit_type == wanted_type and habit_id not in keep_ids:
                keep_ids.append(habit_id)
                break

    # Если одного из типов нет — добираем до двух старейших.
    for habit_id, _ in habits:
        if len(keep_ids) >= 2:
            break
        if habit_id not in keep_ids:
            keep_ids.append(habit_id)

    cursor.execute(
        """
        UPDATE habits
        SET pro_status = 'frozen'
        WHERE user_id = ?
        AND active = 1
        """,
        (user_id,),
    )
    habits_frozen = cursor.rowcount

    for habit_id in keep_ids:
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

    # -----------------------------------------------------
    # ЦЕЛИ
    # -----------------------------------------------------
    cursor.execute(
        """
        SELECT id, is_main
        FROM goals
        WHERE user_id = ?
        AND active = 1
        ORDER BY is_main DESC, id ASC
        """,
        (user_id,),
    )
    goals = cursor.fetchall()

    main_goal_id = goals[0][0] if goals else None

    cursor.execute(
        """
        UPDATE goals
        SET pro_status = 'frozen'
        WHERE user_id = ?
        AND active = 1
        """,
        (user_id,),
    )
    goals_frozen = cursor.rowcount

    if main_goal_id is not None:
        cursor.execute(
            """
            UPDATE goals
            SET pro_status = 'active'
            WHERE id = ?
            AND user_id = ?
            AND active = 1
            """,
            (main_goal_id, user_id),
        )

    conn.commit()
    conn.close()

    return {
        "pro_disabled": bool(pro_disabled),
        "habits_active": len(keep_ids),
        "habits_frozen": max(0, habits_frozen - len(keep_ids)),
        "goals_active": 1 if main_goal_id is not None else 0,
        "goals_frozen": max(0, goals_frozen - (1 if main_goal_id is not None else 0)),
    }
