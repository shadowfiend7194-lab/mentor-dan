from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from services.subscription import user_has_pro

from database.goals import (
    get_user_goals,
    deactivate_goal,
)


# =========================================================
# СПИСОК ЦЕЛЕЙ ДЛЯ УДАЛЕНИЯ
# =========================================================

async def open_goal_delete_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    pro_active = bool(user_has_pro(user_id))

    goals = [
        goal
        for goal in get_user_goals(user_id)
        if pro_active or goal.get("pro_status") != "frozen"
    ]

    # -----------------------------------------------------
    # НЕТ ДОСТУПНЫХ ЦЕЛЕЙ
    # -----------------------------------------------------

    if not goals:

        await query.edit_message_text(
            "🗑 <b>Удаление цели</b>\n\n"
            "У тебя пока нет активных целей.",
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

    # -----------------------------------------------------
    # СПИСОК ЦЕЛЕЙ
    # -----------------------------------------------------

    keyboard = []

    for goal in goals:

        icon = (
            "⭐"
            if goal.get("is_main")
            else
            "🎯"
        )

        title = (
            goal.get("title")
            or "Без названия"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {title}",
                    callback_data=(
                        f"goal_delete_{goal['id']}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="goal_edit"
            )
        ]
    )

    await query.edit_message_text(
        "🗑 <b>Удаление цели</b>\n\n"
        "Выбери цель, которую хочешь удалить:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# =========================================================

async def confirm_goal_delete(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        goal_id = int(
            query.data.replace(
                "goal_delete_",
                ""
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return

    user_id = update.effective_user.id

    goals = get_user_goals(
        user_id
    )

    goal = next(
        (
            item
            for item in goals
            if item.get("id") == goal_id
        ),
        None
    )

    # -----------------------------------------------------
    # ЦЕЛЬ НЕ НАЙДЕНА
    # -----------------------------------------------------

    if not goal:

        await query.edit_message_text(
            "❌ Эта цель уже не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ К списку целей",
                            callback_data="goal_edit"
                        )
                    ]
                ]
            )
        )

        return

    if (
        goal.get("pro_status") == "frozen"
        and not user_has_pro(user_id)
    ):

        await query.edit_message_text(
            "🔒 <b>Цель заморожена</b>\n\n"
            "Удалить её можно только при активном PRO.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data="goal_edit")]]
            )
        )

        return

    goal_title = (
        goal.get("title")
        or "Без названия"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🗑 Да, удалить",
                callback_data=(
                    f"goal_delete_confirm_{goal_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ Отмена",
                callback_data="goal_edit"
            )
        ],
    ]

    await query.edit_message_text(
        "🗑 <b>Удаление цели</b>\n\n"
        f"🎯 <b>{goal_title}</b>\n\n"
        "Ты точно хочешь удалить эту цель?\n\n"
        "Она перестанет отображаться среди активных целей.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ФАКТИЧЕСКОЕ УДАЛЕНИЕ
# =========================================================

async def delete_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        goal_id = int(
            query.data.replace(
                "goal_delete_confirm_",
                ""
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return

    user_id = update.effective_user.id

    goals = get_user_goals(
        user_id
    )

    goal = next(
        (
            item
            for item in goals
            if item.get("id") == goal_id
        ),
        None
    )

    # -----------------------------------------------------
    # ЦЕЛЬ УЖЕ УДАЛЕНА
    # -----------------------------------------------------

    if not goal:

        await query.edit_message_text(
            "❌ Эта цель уже удалена.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ К списку целей",
                            callback_data="goal_edit"
                        )
                    ]
                ]
            )
        )

        return

    goal_title = (
        goal.get("title")
        or "Без названия"
    )

    # -----------------------------------------------------
    # УДАЛЯЕМ
    # -----------------------------------------------------

    deactivate_goal(
        user_id,
        goal_id
    )

    # -----------------------------------------------------
    # ФИНАЛ
    # -----------------------------------------------------

    await query.edit_message_text(
        "🗑 <b>Цель удалена.</b>\n\n"
        f"🎯 {goal_title}\n\n"
        "Связанные с ней привычки не удалены.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✏️ Изменить цели",
                        callback_data="goal_edit"
                    )
                ],
            ]
        )
    )