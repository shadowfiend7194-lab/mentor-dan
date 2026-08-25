from datetime import datetime

from database.connection import get_connection


# =========================================================
# СОХРАНИТЬ В ПАМЯТЬ
# =========================================================

def save_memory(
    user_id,
    memory_key,
    memory_value,
    importance=5,
):
    """
    Сохраняет важный факт о пользователе.

    memory_key:
        название факта

    memory_value:
        содержание факта

    importance:
        важность от 1 до 10
    """

    if not memory_key or not memory_value:
        return

    importance = max(
        1,
        min(10, int(importance))
    )

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM dan_memory

        WHERE user_id = ?
        AND memory_key = ?

        """,
        (
            user_id,
            memory_key,
        )
    )

    row = cursor.fetchone()

    # -----------------------------------------------------
    # ПАМЯТЬ УЖЕ ЕСТЬ — ОБНОВЛЯЕМ
    # -----------------------------------------------------

    if row:

        cursor.execute(
            """
            UPDATE dan_memory

            SET
                memory_value = ?,
                importance = ?,
                updated_at = ?

            WHERE id = ?

            """,
            (
                memory_value,
                importance,
                now,
                row[0],
            )
        )

    # -----------------------------------------------------
    # НОВАЯ ПАМЯТЬ
    # -----------------------------------------------------

    else:

        cursor.execute(
            """
            INSERT INTO dan_memory
            (
                user_id,
                memory_key,
                memory_value,
                importance,
                created_at,
                updated_at
            )

            VALUES (?, ?, ?, ?, ?, ?)

            """,
            (
                user_id,
                memory_key,
                memory_value,
                importance,
                now,
                now,
            )
        )

    conn.commit()
    conn.close()


# =========================================================
# ПОЛУЧИТЬ ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def get_memories(
    user_id,
    limit=50,
):
    """
    Возвращает важные факты о пользователе.

    Более важные воспоминания идут первыми.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            memory_key,
            memory_value,
            importance,
            created_at,
            updated_at

        FROM dan_memory

        WHERE user_id = ?

        ORDER BY
            importance DESC,
            updated_at DESC

        LIMIT ?

        """,
        (
            user_id,
            limit,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# =========================================================
# ПОЛУЧИТЬ ОДНУ ПАМЯТЬ
# =========================================================

def get_memory(
    user_id,
    memory_key,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            memory_key,
            memory_value,
            importance,
            created_at,
            updated_at

        FROM dan_memory

        WHERE user_id = ?
        AND memory_key = ?

        LIMIT 1

        """,
        (
            user_id,
            memory_key,
        )
    )

    row = cursor.fetchone()

    conn.close()

    return row


# =========================================================
# УДАЛИТЬ ОДНУ ПАМЯТЬ
# =========================================================

def delete_memory(
    user_id,
    memory_key,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM dan_memory

        WHERE user_id = ?
        AND memory_key = ?

        """,
        (
            user_id,
            memory_key,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# ОЧИСТИТЬ ВСЮ ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def clear_memories(
    user_id,
):
    """
    Полностью удаляет долгосрочную память Дэна
    конкретного пользователя.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM dan_memory

        WHERE user_id = ?

        """,
        (
            user_id,
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# КОЛИЧЕСТВО ВОСПОМИНАНИЙ
# =========================================================

def get_memory_count(
    user_id,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM dan_memory

        WHERE user_id = ?

        """,
        (
            user_id,
        )
    )

    result = cursor.fetchone()

    conn.close()

    return (
        result[0]
        if result
        else 0
    )