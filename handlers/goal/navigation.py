from telegram import Update

from telegram.ext import ContextTypes


# =========================================================
# НАЗАД К «МОЕЙ ЦЕЛИ»
# =========================================================

async def goal_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    from handlers.goal.screen import show_goal

    await show_goal(
        update,
        context
    )


# =========================================================
# ИЗМЕНЕНИЕ ЦЕЛИ
# =========================================================

async def open_goal_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ Изменить текущую цель",
                callback_data="goal_edit_current"
            )
        ],
        [
            InlineKeyboardButton(
                "⭐ Добавить новую цель PRO",
                callback_data="goal_add_pro"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="goal_back"
            )
        ],
    ]

    await query.message.reply_text(
        "🎯 <b>Изменение цели</b>\n\n"
        "Что хочешь сделать?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# УПРАВЛЕНИЕ ПРИВЫЧКАМИ
# =========================================================

async def open_habit_management(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Добавить новую привычку ⭐ PRO",
                callback_data="habit_add_pro"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ Изменить текущую привычку",
                callback_data="habit_edit"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="goal_back"
            )
        ],
    ]

    await query.message.reply_text(
        "🔄 <b>Управление привычками</b>\n\n"
        "Что хочешь сделать?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )