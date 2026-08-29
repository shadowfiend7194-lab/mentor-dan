from database.connection import get_connection
from services.subscription import disable_test_pro


# =========================================================
# ПОЛНЫЙ СБРОС PRO ДЛЯ ТЕСТИРОВАНИЯ
# =========================================================
#
# Что делает:
#
# 1. Отключает PRO.
# 2. Сбрасывает PRO-персонализацию привычек:
#    - difficulty
#    - motivation
#    - goal_id
#    - pro_status
#
# 3. НЕ удаляет:
#    - привычки
#    - цели
#    - выполнения привычек
#    - историю
#    - достижения
#    - пользователя
#
# После этого можно заново включить тестовый PRO
# и пройти новый сценарий персонализации.
#
# =========================================================


def reset_pro_for_test(user_id):
    """
    Полностью возвращает пользователя
    в состояние перед первым прохождением PRO.

    Использовать ТОЛЬКО для тестирования.
    """

    # -----------------------------------------------------
    # 1. ОТКЛЮЧАЕМ PRO
    # -----------------------------------------------------

    pro_disabled = disable_test_pro(
        user_id
    )

    # -----------------------------------------------------
    # 2. СБРАСЫВАЕМ PRO-ДАННЫЕ ПРИВЫЧЕК
    # -----------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET
            difficulty = NULL,
            motivation = NULL,
            goal_id = NULL,
            pro_status = 'frozen'
        WHERE user_id = ?
        AND active = 1
        """,
        (
            user_id,
        ),
    )

    habits_reset = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "pro_disabled": bool(
            pro_disabled
        ),
        "habits_reset": habits_reset,
    }