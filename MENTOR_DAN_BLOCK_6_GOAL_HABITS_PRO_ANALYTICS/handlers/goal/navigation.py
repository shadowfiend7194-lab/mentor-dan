from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.goals import (
    get_user_goals_for_plan,
    get_user_goals,
    FREE_MAX_GOALS,
    PRO_MAX_GOALS,
)

from services.subscription import (
    user_has_pro,
)


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
# МЕНЮ «ИЗМЕНИТЬ ЦЕЛЬ»
# =========================================================

async def open_goal_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    pro_active = bool(
        user_has_pro(user_id)
    )

    goals = get_user_goals_for_plan(
        user_id,
        include_frozen=pro_active,
    )

    keyboard = []

    # -----------------------------------------------------
    # НЕТ ДОСТУПНЫХ ЦЕЛЕЙ
    # -----------------------------------------------------

    if not goals:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "➕ Добавить цель",
                    callback_data="goal_add_pro"
                )
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data="goal_back"
                )
            ]
        )

        await query.edit_message_text(
            "🎯 <b>Изменение цели</b>\n\n"
            "У тебя пока нет доступных целей для изменения.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # -----------------------------------------------------
    # СПИСОК ЦЕЛЕЙ
    # -----------------------------------------------------

    for goal in goals:

        marker = (
            "⭐"
            if goal.get("is_main")
            else
            "🎯"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{marker} "
                    f"{goal.get('title', 'Без названия')}",
                    callback_data=(
                        f"goal_manage_{goal['id']}"
                    )
                )
            ]
        )

    max_goals = PRO_MAX_GOALS if pro_active else FREE_MAX_GOALS

    if len(goals) < max_goals:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "➕ Добавить цель",
                    callback_data="goal_add_pro"
                )
            ]
        )

    # -----------------------------------------------------
    # НАЗАД
    # -----------------------------------------------------

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="goal_back"
            )
        ]
    )

    await query.edit_message_text(
        "✏️ <b>Изменение цели</b>\n\n"
        "Выбери цель, которую хочешь изменить:",
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


# =========================================================
# ДОБАВЛЕНИЕ ЦЕЛИ ИЗ «МОЯ ЦЕЛЬ»
# =========================================================

async def open_goal_add(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id
    pro_active = user_has_pro(user_id)

    goals = get_user_goals(user_id)

    max_goals = (
        PRO_MAX_GOALS
        if pro_active
        else FREE_MAX_GOALS
    )

    if len(goals) >= max_goals:

        if pro_active:
            text = (
                "🧠 <b>Стоп.</b>\n\n"
                "У тебя уже 3 цели — это максимум.\n\n"
                "Не стоит распыляться на всё сразу. "
                "Лучше сфокусироваться на действительно "
                "важных направлениях и довести их до результата."
            )
        else:
            text = (
                "⭐ <b>Добавление дополнительных целей доступно в PRO</b>\n\n"
                "С активным PRO ты можешь работать "
                "с несколькими целями одновременно."
            )

        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Назад",
                            callback_data="goal_edit"
                        )
                    ]
                ]
            )
        )

        return

    context.user_data[
        "goal_add_state"
    ] = "waiting"

    await query.message.reply_text(
        "➕ <b>Новая цель</b>\n\n"
        "Напиши её своими словами.\n\n"
        "Например:\n"
        "• Улучшить физическую форму\n"
        "• Наладить финансовое положение\n"
        "• Поступить в вуз",
        parse_mode="HTML"
    )
