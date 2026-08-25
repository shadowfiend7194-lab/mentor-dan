from database.dan.memory import (
    get_memories,
    save_memory,
    delete_memory,
    clear_memories,
    get_memory,
    get_memory_count,
)


# =========================================================
# СОХРАНИТЬ ПАМЯТЬ
# =========================================================

def remember(
    user_id,
    key,
    value,
    importance=5,
):
    """
    Сохраняет долгосрочную память пользователя.
    """

    save_memory(
        user_id=user_id,
        memory_key=key,
        memory_value=value,
        importance=importance,
    )


# =========================================================
# ПОЛУЧИТЬ ПАМЯТЬ
# =========================================================

def get_user_memories(
    user_id,
    limit=30,
):
    """
    Возвращает долгосрочную память пользователя.
    """

    rows = get_memories(
        user_id,
        limit,
    )

    return [
        {
            "key": row[0],
            "value": row[1],
            "importance": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }
        for row in rows
    ]


# =========================================================
# ПОЛУЧИТЬ ОДНУ ПАМЯТЬ
# =========================================================

def get_user_memory(
    user_id,
    key,
):
    """
    Возвращает одно конкретное воспоминание.
    """

    row = get_memory(
        user_id,
        key,
    )

    if not row:
        return None

    return {
        "key": row[0],
        "value": row[1],
        "importance": row[2],
        "created_at": row[3],
        "updated_at": row[4],
    }


# =========================================================
# УДАЛИТЬ ПАМЯТЬ
# =========================================================

def forget(
    user_id,
    key,
):
    """
    Удаляет одно воспоминание.
    """

    delete_memory(
        user_id,
        key,
    )


# =========================================================
# ОЧИСТИТЬ ПАМЯТЬ
# =========================================================

def forget_all(
    user_id,
):
    """
    Полностью очищает долгосрочную память пользователя.
    """

    clear_memories(
        user_id,
    )


# =========================================================
# КОЛИЧЕСТВО ВОСПОМИНАНИЙ
# =========================================================

def memory_count(
    user_id,
):
    return get_memory_count(
        user_id,
    )