from services.dan.personality import DAN_PERSONALITY


def _section(title, value):
    return f"\n{title}:\n{value}\n"


def build_dan_prompt(context, user_message, context_level="conversation"):
    profile = context.get("profile", {})
    goals = context.get("goals", [])
    habits = context.get("habits", [])
    habit_trends = context.get("habit_trends", {})
    current_state = context.get("current_state", {})
    statistics = context.get("statistics", {})
    checkin_trends = context.get("checkin_trends", {})
    memories = context.get("memories", [])
    conversation = context.get("conversation", [])

    parts = [
        DAN_PERSONALITY,
        "\nРЕЖИМ КОНТЕКСТА:",
        context_level,
        "\nВАЖНО: текущая реплика пользователя всегда имеет приоритет.",
    ]

    if profile:
        parts.append(_section("ПРОФИЛЬ", profile))

    if goals:
        parts.append(_section("ЦЕЛИ", goals))

    if habits:
        parts.append(_section("ПРИВЫЧКИ", habits))

    if current_state:
        parts.append(_section("ТЕКУЩЕЕ СОСТОЯНИЕ", current_state))

    if statistics:
        parts.append(_section("СТАТИСТИКА", statistics))

    if habit_trends:
        parts.append(_section("ТРЕНДЫ ПРИВЫЧЕК", habit_trends))

    if checkin_trends:
        parts.append(_section("ТРЕНДЫ ЧЕК-ИНОВ", checkin_trends))

    if memories:
        parts.append(_section("ПАМЯТЬ", memories))

    if conversation:
        parts.append(_section("ПОСЛЕДНИЙ ДИАЛОГ", conversation))

    parts.append(
        "\nНе пересказывай контекст. Используй его только там, где он "
        "делает ответ точнее или полезнее."
    )
    parts.append(
        "\nНе заканчивай ответ вопросом автоматически."
    )
    parts.append(
        "\nЕсли данных недостаточно, не додумывай — скажи это прямо."
    )

    # Текущая реплика передаётся отдельно в API как user-message.
    # Здесь она не дублируется.
    return "".join(parts).strip()
