from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

from services.dan.pro_habits import (
    get_available_goals,
    get_habit_goal,
    set_habit_goal,
    remove_habit_goal,
    update_habit_pro_data,
    get_habit_pro_data,
)


# =========================================================
# ВЫБОР ЦЕЛИ ДЛЯ ПРИВЫЧКИ
# =========================================================

async def show_habit_goal_selection(
    update,
    context,
    habit_id,
):
    """
    Показывает пользователю список целей,
    к которым можно привязать привычку.
    """

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    goals = get_available_goals(user_id)

    if not goals:

        keyboard = [
            [
                InlineKeyboardButton(
                    "↩️ Назад",
                    callback_data=(
                        f"habit_pro_back:{habit_id}"
                    ),
                )
            ]
        ]

        await query.edit_message_text(
            "🎯 У тебя пока нет доступных целей.\n\n"
            "Создай цель, чтобы привязать к ней привычку.",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return


    keyboard = []

    for goal in goals:

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🎯 {goal['title']}",
                    callback_data=(
                        f"habit_goal_set:"
                        f"{habit_id}:"
                        f"{goal['id']}"
                    ),
                )
            ]
        )


    keyboard.append(
        [
            InlineKeyboardButton(
                "🧠 Для себя",
                callback_data=(
                    f"habit_goal_none:{habit_id}"
                ),
            )
        ]
    )


    keyboard.append(
        [
            InlineKeyboardButton(
                "↩️ Назад",
                callback_data=(
                    f"habit_pro_back:{habit_id}"
                ),
            )
        ]
    )


    await query.edit_message_text(
        "🎯 К чему относится эта привычка?\n\n"
        "Выбери цель, которой она помогает "
        "достигать.\n\n"
        "Или выбери «Для себя», если привычка "
        "не связана напрямую с конкретной целью.",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# =========================================================
# УСТАНОВКА ЦЕЛИ
# =========================================================

async def set_habit_goal_callback(
    update,
    context,
):
    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    parts = query.data.split(":")

    if len(parts) != 3:
        return

    try:
        habit_id = int(parts[1])
        goal_id = int(parts[2])

    except ValueError:
        return


    success = set_habit_goal(
        habit_id,
        user_id,
        goal_id,
    )


    if not success:

        await query.edit_message_text(
            "Не удалось привязать привычку к цели."
        )

        return


    await query.edit_message_text(
        "✅ Привычка привязана к цели.\n\n"
        "Теперь её выполнение будет учитываться "
        "в системе прогресса этой цели."
    )


# =========================================================
# ОТВЯЗКА ОТ ЦЕЛИ
# =========================================================

async def remove_habit_goal_callback(
    update,
    context,
):
    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    parts = query.data.split(":")

    if len(parts) != 2:
        return

    try:
        habit_id = int(parts[1])

    except ValueError:
        return


    success = remove_habit_goal(
        habit_id,
        user_id,
    )


    if not success:

        await query.edit_message_text(
            "Не удалось изменить связь привычки."
        )

        return


    await query.edit_message_text(
        "✅ Связь с целью убрана.\n\n"
        "Привычка продолжает работать как обычно."
    )


# =========================================================
# НАЗАД
# =========================================================

async def habit_pro_back(
    update,
    context,
):
    query = update.callback_query

    await query.answer()

    habit_id = query.data.split(":")[1]

    await query.edit_message_text(
        "⚙️ Настройки PRO привычки\n\n"
        "Здесь можно настроить дополнительные "
        "параметры привычки."
    )


# =========================================================
# REGISTRATION
# =========================================================

def get_pro_habit_handlers():

    return [
        CallbackQueryHandler(
            set_habit_goal_callback,
            pattern=r"^habit_goal_set:\d+:\d+$",
        ),

        CallbackQueryHandler(
            remove_habit_goal_callback,
            pattern=r"^habit_goal_none:\d+$",
        ),

        CallbackQueryHandler(
            habit_pro_back,
            pattern=r"^habit_pro_back:\d+$",
        ),
    ]