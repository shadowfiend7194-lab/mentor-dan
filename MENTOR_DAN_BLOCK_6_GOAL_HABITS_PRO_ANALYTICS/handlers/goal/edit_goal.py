from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.goals import (
    get_user_goals,
    create_goal,
    update_goal,
    FREE_MAX_GOALS,
    PRO_MAX_GOALS,
)

from services.subscription import (
    user_has_pro,
)


# =========================================================
# ПОЛУЧИТЬ ЦЕЛЬ
# =========================================================

def get_goal_by_id(
    user_id,
    goal_id
):

    try:

        goal_id = int(
            goal_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    goals = get_user_goals(
        user_id
    )

    return next(
        (
            goal
            for goal in goals
            if goal.get("id") == goal_id
        ),
        None
    )


# =========================================================
# МЕНЮ КОНКРЕТНОЙ ЦЕЛИ
# =========================================================

async def open_goal_manage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    try:

        goal_id = int(
            query.data.rsplit(
                "_",
                1
            )[1]
        )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):

        return

    goal = get_goal_by_id(
        user_id,
        goal_id
    )

    if not goal:

        await query.edit_message_text(
            "❌ Эта цель не найдена.",
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

    if (
        goal.get("pro_status") == "frozen"
        and not user_has_pro(user_id)
    ):

        await query.edit_message_text(
            "🔒 <b>Цель заморожена</b>\n\n"
            "Эта цель была создана или сохранена в PRO.\n"
            "После окончания PRO её нельзя изменять или удалять.",
            parse_mode="HTML",
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

    marker = (
        "⭐"
        if goal.get("is_main")
        else
        "🎯"
    )

    title = (
        goal.get("title")
        or "Без названия"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ Изменить название",
                callback_data=(
                    f"goal_rename_{goal_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить цель",
                callback_data=(
                    f"goal_delete_{goal_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ К списку целей",
                callback_data="goal_edit"
            )
        ],
    ]

    await query.edit_message_text(
        "🎯 <b>Управление целью</b>\n\n"
        f"{marker} <b>{title}</b>\n\n"
        "Что хочешь сделать?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# НАЧАТЬ ПЕРЕИМЕНОВАНИЕ
# =========================================================

async def edit_selected_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    try:

        goal_id = int(
            query.data.rsplit(
                "_",
                1
            )[1]
        )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):

        return

    goal = get_goal_by_id(
        user_id,
        goal_id
    )

    if not goal:

        await query.message.reply_text(
            "❌ Эта цель уже не найдена."
        )

        return

    if (
        goal.get("pro_status") == "frozen"
        and not user_has_pro(user_id)
    ):

        await query.message.reply_text(
            "🔒 Эта цель заморожена после окончания PRO. "
            "Изменять её можно только с активным PRO."
        )

        return

    context.user_data[
        "goal_edit_state"
    ] = "waiting"

    context.user_data[
        "goal_edit_id"
    ] = goal_id

    await query.message.reply_text(
        "✏️ <b>Изменение цели</b>\n\n"
        f"Сейчас: <b>{goal.get('title', 'Без названия')}</b>\n\n"
        "Напиши новую формулировку цели.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Отмена",
                        callback_data=(
                            f"goal_manage_{goal_id}"
                        )
                    )
                ]
            ]
        )
    )


# =========================================================
# СОХРАНИТЬ НОВОЕ НАЗВАНИЕ
# =========================================================

async def save_edited_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "goal_edit_state"
    ) != "waiting":

        return False

    goal_id = context.user_data.get(
        "goal_edit_id"
    )

    if goal_id is None:
        return False

    new_goal = (
        update.message.text.strip()
    )

    if not new_goal:

        await update.message.reply_text(
            "Напиши новую формулировку цели."
        )

        return True

    user_id = update.effective_user.id

    goal = get_goal_by_id(
        user_id,
        goal_id
    )

    if not goal:

        context.user_data.pop(
            "goal_edit_state",
            None
        )

        context.user_data.pop(
            "goal_edit_id",
            None
        )

        await update.message.reply_text(
            "❌ Эта цель больше не найдена."
        )

        return True

    updated = update_goal(
        user_id=user_id,
        goal_id=goal_id,
        title=new_goal,
    )

    context.user_data.pop(
        "goal_edit_state",
        None
    )

    context.user_data.pop(
        "goal_edit_id",
        None
    )

    if not updated:

        await update.message.reply_text(
            "❌ Не получилось обновить цель."
        )

        return True

    await update.message.reply_text(
        "✅ <b>Цель обновлена.</b>\n\n"
        f"🎯 {new_goal}",
        parse_mode="HTML"
    )

    from handlers.goal.screen import show_goal

    await show_goal(
        update,
        context
    )

    return True


# =========================================================
# СОЗДАТЬ НОВУЮ ЦЕЛЬ
# =========================================================

async def save_new_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "goal_add_state"
    ) != "waiting":

        return False

    title = (
        update.message.text.strip()
    )

    if not title:

        await update.message.reply_text(
            "Напиши название цели."
        )

        return True

    user_id = update.effective_user.id

    goals = get_user_goals(
        user_id
    )

    pro_active = user_has_pro(user_id)
    max_goals = (
        PRO_MAX_GOALS
        if pro_active
        else FREE_MAX_GOALS
    )

    if len(goals) >= max_goals:

        context.user_data.pop(
            "goal_add_state",
            None
        )

        await update.message.reply_text(
            "🧠 <b>У тебя уже 3 цели.</b>\n\n"
            "Это максимум. Лучше не распыляться "
            "и сосредоточиться на действительно важных "
            "направлениях.",
            parse_mode="HTML"
        )

        return True

    goal_id = create_goal(
        user_id=user_id,
        title=title,
        is_main=(len(goals) == 0),
    )

    context.user_data.pop(
        "goal_add_state",
        None
    )

    if goal_id is None:

        await update.message.reply_text(
            "❌ Не получилось создать цель.\n\n"
            "Возможно, достигнут лимит в 3 цели."
        )

        return True

    await update.message.reply_text(
        "✅ <b>Цель добавлена.</b>\n\n"
        f"🎯 {title}",
        parse_mode="HTML"
    )

    from handlers.goal.screen import show_goal

    await show_goal(
        update,
        context
    )

    return True


# =========================================================
# ТЕКСТОВОЙ РОУТЕР ЦЕЛЕЙ
# =========================================================

async def goal_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if context.user_data.get(
        "goal_edit_state"
    ) == "waiting":

        return await save_edited_goal(
            update,
            context
        )

    if context.user_data.get(
        "goal_add_state"
    ) == "waiting":

        return await save_new_goal(
            update,
            context
        )

    return False