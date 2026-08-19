from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import (
    get_user_habits,
    format_frequency,
)

from database.goals import get_main_goal


# =========================================================
# ЭКРАН «МОЯ ЦЕЛЬ»
# =========================================================

async def show_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    force_new=False
):

    user_id = update.effective_user.id


    # =====================================================
    # ЦЕЛЬ
    # =====================================================

    goal_data = get_main_goal(
        user_id
    )

    if goal_data:

        goal = goal_data["title"]

    else:

        goal = context.user_data.get(
            "main_goal"
        )


    if not goal:

        goal = (
            "🏆 Активной цели сейчас нет.\n\n"
            "Предыдущая цель завершена. "
            "Когда появится новая — мы начнём следующий этап."
        )


    # =====================================================
    # ПРИВЫЧКИ
    # =====================================================

    habits = get_user_habits(
        user_id
    )


    good_habits = [
        habit
        for habit in habits
        if (
            habit["habit_type"] == "good"
            and not habit.get("formed")
        )
    ]

    bad_habits = [
        habit
        for habit in habits
        if (
            habit["habit_type"] == "bad"
            and not habit.get("controlled")
        )
    ]


    # =====================================================
    # ТЕКСТ
    # =====================================================

    text = (
        "🎯 <b>Моя цель</b>\n\n"
        f"<b>Главная цель:</b>\n"
        f"{goal}\n\n"
    )


    # =====================================================
    # ПОЛЕЗНЫЕ ПРИВЫЧКИ
    # =====================================================

    text += (
        "🟢 <b>Полезные привычки:</b>\n\n"
    )


    if good_habits:

        for habit in good_habits:

            text += (
                f"🟢 {habit['name']}\n"
                f"📅 {format_frequency(habit['frequency'], habit.get('schedule_days'))}\n\n"
            )

    else:

        text += (
            "Пока нет полезных привычек.\n\n"
        )


    # =====================================================
    # НЕЖЕЛАТЕЛЬНЫЕ ПРИВЫЧКИ
    # =====================================================

    text += (
        "🔴 <b>Нежелательные привычки:</b>\n\n"
    )


    if bad_habits:

        for habit in bad_habits:

            text += (
                f"🔴 {habit['name']}\n"
                f"📅 {format_frequency(habit['frequency'], habit.get('schedule_days'))}\n\n"
            )

    else:

        text += (
            "Пока нет нежелательных привычек.\n\n"
        )


    # =====================================================
    # КНОПКИ
    # =====================================================

    keyboard = [

        [
            InlineKeyboardButton(
                "✏️ Изменить цель",
                callback_data="goal_edit"
            )
        ],

        [
            InlineKeyboardButton(
                "🔄 Изменить привычки",
                callback_data="goal_habits"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="go_menu"
            )
        ],

    ]


    markup = InlineKeyboardMarkup(
        keyboard
    )


    # =====================================================
    # РЕДАКТИРОВАНИЕ СООБЩЕНИЯ
    # =====================================================

    if update.callback_query and not force_new:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )