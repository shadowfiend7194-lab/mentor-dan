from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import create_habit, parse_custom_days


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


    if text.lower() in [
        "нет",
        "нету",
        "нет.",
        "пока нет",
        "пока нет.",
    ]:

        context.user_data["good_habit"] = None

        context.user_data[
            "onboarding_step"
        ] = "bad_habit"


        await ask_bad_habit(
            update,
            context
        )

        return



    context.user_data[
        "good_habit"
    ] = text


    context.user_data[
        "onboarding_step"
    ] = "good_habit_frequency"



    await ask_frequency(
        update,
        context,
        "good"
    )



# =========================================================
# ЧАСТОТА ПОЛЕЗНОЙ
# =========================================================

async def handle_good_habit_frequency_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return


    await query.answer()



    if query.data == "good_frequency_daily":

        frequency = "daily"
        schedule_days = None


    elif query.data == "good_frequency_weekdays":

        frequency = "weekdays"
        schedule_days = None


    elif query.data == "good_frequency_custom":

        context.user_data[
            "onboarding_step"
        ] = "good_habit_custom_frequency"


        await query.message.reply_text(
            "Напиши дни.\n\n"
            "Например: Пн, Ср, Пт"
        )

        return


    else:
        return



    create_habit(
        user_id=update.effective_user.id,
        name=context.user_data["good_habit"],
        habit_type="good",
        frequency=frequency,
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
# СВОИ ДНИ ПОЛЕЗНОЙ
# =========================================================

async def handle_good_habit_custom_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    days = parse_custom_days(
        update.message.text
    )


    if not days:

        await update.message.reply_text(
            "Не понял дни 😕\n"
            "Например: Пн, Ср, Пт"
        )

        return



    schedule_days = ",".join(
        map(str, days)
    )



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
# ПЛОХАЯ ПРИВЫЧКА
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
        "Есть ли привычка, от которой ты хочешь избавиться?\n\n"
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
# ВЫБОР ПЛОХОЙ
# =========================================================

async def handle_bad_habit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if not query:
        return


    await query.answer()



    if query.data == "bad_habit_no":


        context.user_data[
            "onboarding_step"
        ] = "oath"


        from handlers.onboarding.oath import show_oath


        await show_oath(
            update,
            context
        )

        return



    if query.data == "bad_habit_yes":


        context.user_data[
            "onboarding_step"
        ] = "bad_habit_name"


        await query.message.reply_text(
            "Напиши плохую привычку."
        )



# =========================================================
# НАЗВАНИЕ ПЛОХОЙ
# =========================================================

async def handle_bad_habit_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return



    context.user_data[
        "bad_habit"
    ] = update.message.text.strip()



    context.user_data[
        "onboarding_step"
    ] = "bad_habit_frequency"



    await ask_frequency(
        update,
        context,
        "bad"
    )



# =========================================================
# ЧАСТОТА ПЛОХОЙ
# =========================================================

async def handle_bad_habit_frequency_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if not query:
        return


    await query.answer()



    if query.data == "bad_frequency_daily":

        frequency = "daily"
        schedule_days = None


    elif query.data == "bad_frequency_weekdays":

        frequency = "weekdays"
        schedule_days = None


    elif query.data == "bad_frequency_custom":


        context.user_data[
            "onboarding_step"
        ] = "bad_habit_custom_frequency"


        await query.message.reply_text(
            "Напиши дни.\n"
            "Например: Пн, Ср, Пт"
        )


        return


    else:
        return



    create_habit(
        user_id=update.effective_user.id,
        name=context.user_data["bad_habit"],
        habit_type="bad",
        frequency=frequency,
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
# СВОИ ДНИ ПЛОХОЙ
# =========================================================

async def handle_bad_habit_custom_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return



    days = parse_custom_days(
        update.message.text
    )



    if not days:

        await update.message.reply_text(
            "Не понял дни 😕"
        )

        return



    schedule_days = ",".join(
        map(str, days)
    )



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
# КНОПКИ ЧАСТОТЫ
# =========================================================

async def ask_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    habit_type: str
):

    prefix = (
        "good"
        if habit_type == "good"
        else
        "bad"
    )



    keyboard = [

        [
            InlineKeyboardButton(
                "📅 Каждый день",
                callback_data=f"{prefix}_frequency_daily"
            )
        ],

        [
            InlineKeyboardButton(
                "🗓️ Пн–Пт",
                callback_data=f"{prefix}_frequency_weekdays"
            )
        ],

        [
            InlineKeyboardButton(
                "✏️ Свои дни",
                callback_data=f"{prefix}_frequency_custom"
            )
        ],

    ]



    await update.effective_message.reply_text(

        "📅 Выбери периодичность:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )