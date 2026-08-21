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


# =========================================================
# ЭКРАН «МОЙ ДЕНЬ»
# =========================================================

async def show_day(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id


    habits = get_user_habits(
        user_id
    )

    habits = [
        habit
        for habit in get_user_habits(user_id)
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