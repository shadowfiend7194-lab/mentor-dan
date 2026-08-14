from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import create_habit


# =========================================================
# ПОЛЕЗНАЯ ПРИВЫЧКА
# =========================================================

async def handle_good_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    if not text:
        return

    # Пользователь не хочет добавлять полезную привычку
    if text.lower() in [
        "нет",
        "нету",
        "нет.",
        "пока нет",
        "пока нет.",
    ]:

        context.user_data["good_habit"] = None
        context.user_data["good_habit_frequency"] = None

        context.user_data[
            "onboarding_step"
        ] = "bad_habit"

        await ask_bad_habit(
            update,
            context
        )

        return

    # Сохраняем во временное состояние
    context.user_data["good_habit"] = text

    context.user_data[
        "onboarding_step"
    ] = "good_habit_frequency"

    await ask_frequency(
        update,
        context,
        "good"
    )


# =========================================================
# ПЕРИОДИЧНОСТЬ ПОЛЕЗНОЙ ПРИВЫЧКИ
# =========================================================

async def handle_good_habit_frequency_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    # -----------------------------------------------------
    # КАЖДЫЙ ДЕНЬ
    # -----------------------------------------------------

    if query.data == "good_frequency_daily":

        create_habit(
            user_id=update.effective_user.id,
            name=context.user_data["good_habit"],
            habit_type="good",
            frequency="daily",
            schedule_days=None,
        )

    elif query.data == "good_frequency_weekdays":

        create_habit(
            user_id=update.effective_user.id,
            name=context.user_data["good_habit"],
            habit_type="good",
            frequency="weekdays",
            schedule_days=None,
        )

    elif query.data == "good_frequency_custom":

        context.user_data[
            "onboarding_step"
        ] = "good_habit_custom_frequency"

        await query.message.reply_text(
            "✏️ Хорошо.\n\n"
            "Напиши дни, когда хочешь выполнять привычку.\n\n"
            "Например: Пн, Ср, Пт"
        )

        return

    else:
        return

    # -----------------------------------------------------
    # Сохраняем периодичность
    # -----------------------------------------------------

    context.user_data[
        "good_habit_frequency"
    ] = frequency

    # -----------------------------------------------------
    # СОХРАНЯЕМ ПОЛЕЗНУЮ ПРИВЫЧКУ В БД
    # -----------------------------------------------------

    create_habit(
        user_id=update.effective_user.id,
        name=context.user_data["good_habit"],
        habit_type="good",
        frequency=frequency,
    )

    context.user_data[
        "onboarding_step"
    ] = "bad_habit"

    await ask_bad_habit(
        update,
        context
    )


# =========================================================
# СВОИ ДНИ — ПОЛЕЗНАЯ ПРИВЫЧКА
# =========================================================

async def handle_good_habit_custom_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    if not text:
        return

    from database.habits import parse_custom_days

    days = parse_custom_days(
        text
    )

    if not days:

        await update.message.reply_text(
            "Не смог распознать дни. 😕\n\n"
            "Напиши, например:\n"
            "Пн, Ср, Пт"
        )

        return

    schedule_days = ",".join(
        map(str, days)
    )

    context.user_data[
        "good_habit_frequency"
    ] = "custom"

    context.user_data[
        "good_habit_schedule_days"
    ] = schedule_days

    create_habit(
        user_id=update.effective_user.id,
        name=context.user_data["good_habit"],
        habit_type="good",
        frequency="custom",
        schedule_days=schedule_days,
    )

    context.user_data[
        "onboarding_step"
    ] = "bad_habit"

    await ask_bad_habit(
        update,
        context
    )


# =========================================================
# ВОПРОС О ПЛОХОЙ ПРИВЫЧКЕ
# =========================================================

async def ask_bad_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🚫 Да, хочу избавиться",
                callback_data="bad_habit_yes"
            )
        ],
        [
            InlineKeyboardButton(
                "➡️ Нет, такой нет",
                callback_data="bad_habit_no"
            )
        ],
    ]

    await update.effective_message.reply_text(
        "Теперь наоборот. 👀\n\n"
        "Есть ли привычка, от которой ты хочешь "
        "избавиться?\n\n"
        "Например:\n"
        "📱 Меньше сидеть в телефоне\n"
        "🍔 Меньше есть вредной еды\n"
        "🌙 Не ложиться слишком поздно\n"
        "⏳ Не откладывать дела",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ЕСТЬ / НЕТ ПЛОХОЙ ПРИВЫЧКИ
# =========================================================

async def handle_bad_habit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    # -----------------------------------------------------
    # НЕТ ПЛОХОЙ ПРИВЫЧКИ
    # -----------------------------------------------------

    if query.data == "bad_habit_no":

        context.user_data["bad_habit"] = None
        context.user_data[
            "bad_habit_frequency"
        ] = None

        context.user_data[
            "onboarding_step"
        ] = "oath"

        from handlers.onboarding.oath import show_oath

        await show_oath(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # ЕСТЬ ПЛОХАЯ ПРИВЫЧКА
    # -----------------------------------------------------

    if query.data == "bad_habit_yes":

        context.user_data[
            "onboarding_step"
        ] = "bad_habit_name"

        await query.message.reply_text(
            "Понял. 👍\n\n"
            "Напиши, от какой привычки хочешь избавиться.\n\n"
            "Например: постоянно проверять телефон "
            "или откладывать дела до последнего."
        )

        return


# =========================================================
# НАЗВАНИЕ ПЛОХОЙ ПРИВЫЧКИ
# =========================================================

async def handle_bad_habit_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    if not text:
        return

    context.user_data[
        "bad_habit"
    ] = text

    context.user_data[
        "onboarding_step"
    ] = "bad_habit_frequency"

    await ask_frequency(
        update,
        context,
        "bad"
    )


# =========================================================
# ПЕРИОДИЧНОСТЬ ПЛОХОЙ ПРИВЫЧКИ
# =========================================================

async def handle_bad_habit_frequency_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    # -----------------------------------------------------
    # КАЖДЫЙ ДЕНЬ
    # -----------------------------------------------------

    if query.data == "bad_frequency_daily":

        create_habit(
            user_id=update.effective_user.id,
            name=context.user_data["bad_habit"],
            habit_type="bad",
            frequency="daily",
            schedule_days=None,
        )

    elif query.data == "bad_frequency_weekdays":

        create_habit(
            user_id=update.effective_user.id,
            name=context.user_data["bad_habit"],
            habit_type="bad",
            frequency="weekdays",
            schedule_days=None,
        )

    elif query.data == "bad_frequency_custom":

        context.user_data[
            "onboarding_step"
        ] = "bad_habit_custom_frequency"

        await query.message.reply_text(
            "✏️ Хорошо.\n\n"
            "Напиши дни, когда это обычно происходит.\n\n"
            "Например: Пн, Ср, Пт"
        )

        return

    else:
        return

    # -----------------------------------------------------
    # Сохраняем периодичность
    # -----------------------------------------------------

    context.user_data[
        "bad_habit_frequency"
    ] = frequency

    # -----------------------------------------------------
    # СОХРАНЯЕМ ПЛОХУЮ ПРИВЫЧКУ В БД
    # -----------------------------------------------------

    create_habit(
        user_id=update.effective_user.id,
        name=context.user_data["bad_habit"],
        habit_type="bad",
        frequency=frequency,
    )

    context.user_data[
        "onboarding_step"
    ] = "oath"

    from handlers.onboarding.oath import show_oath

    await show_oath(
        update,
        context
    )


# =========================================================
# СВОИ ДНИ — ПЛОХАЯ ПРИВЫЧКА
# =========================================================

async def handle_bad_habit_custom_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    if not text:
        return

    from database.habits import parse_custom_days

    days = parse_custom_days(
        text
    )

    if not days:

        await update.message.reply_text(
            "Не смог распознать дни. 😕\n\n"
            "Напиши, например:\n"
            "Пн, Ср, Пт"
        )

        return

    schedule_days = ",".join(
        map(str, days)
    )

    context.user_data[
        "bad_habit_frequency"
    ] = "custom"

    context.user_data[
        "bad_habit_schedule_days"
    ] = schedule_days

    create_habit(
        user_id=update.effective_user.id,
        name=context.user_data["bad_habit"],
        habit_type="bad",
        frequency="custom",
        schedule_days=schedule_days,
    )

    context.user_data[
        "onboarding_step"
    ] = "oath"

    from handlers.onboarding.oath import show_oath

    await show_oath(
        update,
        context
    )


# =========================================================
# ВЫБОР ПЕРИОДИЧНОСТИ
# =========================================================

async def ask_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    habit_type: str
):

    if habit_type == "good":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📅 Каждый день",
                    callback_data="good_frequency_daily"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗓️ Пн–Пт",
                    callback_data="good_frequency_weekdays"
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ Выбрать дни",
                    callback_data="good_frequency_custom"
                )
            ],
        ]

        text = (
            "📅 Как часто хочешь выполнять эту привычку?\n\n"
            "Выбери удобный ритм:"
        )

    else:

        keyboard = [
            [
                InlineKeyboardButton(
                    "📅 Каждый день",
                    callback_data="bad_frequency_daily"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗓️ Пн–Пт",
                    callback_data="bad_frequency_weekdays"
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ Выбрать дни",
                    callback_data="bad_frequency_custom"
                )
            ],
        ]

        text = (
            "📅 Как часто это обычно происходит?\n\n"
            "Выбери подходящий вариант:"
        )

    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )