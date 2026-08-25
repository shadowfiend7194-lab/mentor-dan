from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


# =========================================================
# НАЧАТЬ ЗНАКОМСТВО
# =========================================================

async def start_intro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    

    context.user_data["onboarding"] = True
    context.user_data["onboarding_step"] = "name"

    await query.message.reply_text(
        "👋 Отлично, тогда начнём спокойно.\n\n"
        "Для начала — как мне тебя называть? 😊"
    )


# =========================================================
# ЗАЧЕМ ЭТО НУЖНО
# =========================================================

async def why_intro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Начать знакомство",
                callback_data="start_intro"
            )
        ]
    ]

    await query.message.reply_text(
        "Дэн — это не просто трекер привычек.\n\n"
        "Я буду помогать тебе понимать, "
        "что происходит с твоей дисциплиной, "
        "где ты проседаешь и что лучше сделать дальше.\n\n"
        "Без попыток изменить всю жизнь за один день.\n\n"
        "Маленькие действия → стабильность → результат. 💪",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# НАЗАД К ПРИВЕТСТВИЮ
# =========================================================

async def back_to_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Начать знакомство",
                callback_data="start_intro"
            )
        ],
        [
            InlineKeyboardButton(
                "🔍 Зачем это нужно?",
                callback_data="why_intro"
            )
        ]
    ]

    await query.message.reply_text(
        "Привет! 👋\n\n"
        "Я Дэн.\n\n"
        "Твой персональный наставник "
        "по дисциплине и развитию.\n\n"
        "Готов? 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )