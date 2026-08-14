import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


async def show_oath(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["onboarding_step"] = "oath"

    keyboard = [
        [
            InlineKeyboardButton(
                "🤝 Я в деле",
                callback_data="oath_accept"
            )
        ]
    ]

    await update.effective_message.reply_text(
        "🫡🔥 <b>Моя клятва</b>\n\n"

        "Я не обязан быть идеальным.\n\n"

        "Я могу ошибаться, срываться и иногда сбиваться с пути.\n"
        "Но я обещаю себе <b>не бросать начатое</b>.\n\n"

        "Если сорвался — вернусь. 🔄\n"
        "Если тяжело — сделаю хотя бы маленький шаг. 👣\n"
        "Если не хочется — вспомню, ради чего начал. 🎯\n\n"

        "Я беру ответственность за свои решения, "
        "свои привычки и свой результат. 💪\n\n"

        "Мне не нужно изменить всю жизнь за один день.\n"
        "Мне нужно становиться "
        "<b>немного лучше каждый день</b>. 📈\n\n"

        "С этого дня я начинаю работать над собой. 🚀\n\n"

        "<b>Я не сдаюсь. Я в деле. 🤝🔥</b>",

        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def accept_oath(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()
    await asyncio.sleep(1)
    context.user_data["oath_accepted"] = True
    context.user_data["onboarding_step"] = "wake_time"

    await query.message.reply_text(
        "🌅 Отлично. Теперь настроим твой режим дня.\n\n"
        "Во сколько ты обычно просыпаешься? ⏰\n\n"
        "Напиши время, например: <b>08:30</b>",
        parse_mode="HTML"
    )