from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import (
    get_user_habits,
    is_completed_today,
    get_habit_streak,
    is_habit_scheduled_today,
)

from services.subscription import get_user_plan


# =========================================================
# ЭКРАН «МОЙ ДЕНЬ»
# =========================================================

async def show_day(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    plan = get_user_plan(user_id)

    all_habits = get_user_habits(user_id)

    frozen_count = sum(
        1
        for habit in all_habits
        if habit.get("pro_status") == "frozen"
    )

    if plan == "pro":
        available_habits = all_habits
    else:
        available_habits = [
            habit
            for habit in all_habits
            if habit.get("pro_status") != "frozen"
        ]

    habits = [
        habit
        for habit in available_habits
        if is_habit_scheduled_today(habit)
    ]


    good_habits = []
    bad_habits = []


    for habit in habits:

        # показываем только если сегодня день привычки

        if not is_habit_scheduled_today(
            habit
        ):
            continue


        if habit["habit_type"] == "good":

            good_habits.append(
                habit
            )


        elif habit["habit_type"] == "bad":

            bad_habits.append(
                habit
            )



    keyboard = []


    # =====================================================
    # ЕСЛИ ЕСТЬ ПРИВЫЧКИ
    # =====================================================

    max_habits = max(
        len(good_habits),
        len(bad_habits)
    )


    for index in range(
        max_habits
    ):

        row = []


        # -------------------------------------------------
        # ХОРОШАЯ ПРИВЫЧКА
        # -------------------------------------------------

        if index < len(good_habits):

            habit = good_habits[index]

            habit_id = habit["id"]


            completed = is_completed_today(
                habit_id
            )


            if completed:

                streak = get_habit_streak(
                    habit_id
                )

                text = (
                    f"🔥 {streak} | {habit['name']} ✅"
                )

            else:

                text = (
                    f"🟢 {habit['name']}"
                )


            row.append(
                InlineKeyboardButton(
                    text,
                    callback_data=f"day_habit_{habit_id}"
                )
            )


        # -------------------------------------------------
        # ПУСТОЕ МЕСТО
        # -------------------------------------------------

        else:

            row.append(
                InlineKeyboardButton(
                    " ",
                    callback_data="day_no_action"
                )
            )



        # -------------------------------------------------
        # ПЛОХАЯ ПРИВЫЧКА
        # -------------------------------------------------

        if index < len(bad_habits):

            habit = bad_habits[index]

            habit_id = habit["id"]


            completed = is_completed_today(
                habit_id
            )


            if completed:

                streak = get_habit_streak(
                    habit_id
                )

                text = (
                    f"🔥 {streak} | {habit['name']} ✅"
                )

            else:

                text = (
                    f"🔴 {habit['name']}"
                )


            row.append(
                InlineKeyboardButton(
                    text,
                    callback_data=f"day_habit_{habit_id}"
                )
            )


        else:

            row.append(
                InlineKeyboardButton(
                    " ",
                    callback_data="day_no_action"
                )
            )


        keyboard.append(
            row
        )



    # =====================================================
    # ЕСЛИ НЕТ ПРИВЫЧЕК СЕГОДНЯ
    # =====================================================

    if not good_habits and not bad_habits:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "✨ Нет задач на сегодня",
                    callback_data="day_no_action"
                )
            ]
        )



    # =====================================================
    # ЧЕК-ИНЫ
    # =====================================================

    keyboard.append(
        [
            InlineKeyboardButton(
                "☀️ Утро",
                callback_data="day_morning"
            ),

            InlineKeyboardButton(
                "🌙 Вечер",
                callback_data="day_evening"
            )
        ]
    )



    keyboard.append(
        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="go_menu"
            )
        ]
    )



    # =====================================================
    # ТЕКСТ
    # =====================================================

    text = (
        "📅 <b>Мой день</b>\n\n"

        "Отмечай выполненные действия сегодня 👇\n\n"

        "🟢 Полезная привычка — нажми после выполнения.\n"

        "🔴 Нежелательная — нажми, если удержался."
    )

    if plan == "pro_expired" and frozen_count:
        text += (
            "\n\n🔒 <b>Заморожено после окончания PRO:</b> "
            f"{frozen_count} привычк(а/и)."
        )



    markup = InlineKeyboardMarkup(
        keyboard
    )



    # =====================================================
    # ОБНОВЛЕНИЕ / ОТКРЫТИЕ
    # =====================================================

    if update.callback_query:

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