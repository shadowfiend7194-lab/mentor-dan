from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.users import get_user
from handlers.menu import show_menu


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    print("🔥 START HANDLER WORKS")

    user_id = update.effective_user.id
    print(f"👤 USER ID: {user_id}")

    user = get_user(user_id)
    print(f"🗄️ USER FROM DB: {user}")


    print("🔥 START HANDLER WORKS")

    user_id = update.effective_user.id

    # Проверяем, есть ли пользователь в базе
    user = get_user(user_id)

    # =====================================================
    # СТАРЫЙ ПОЛЬЗОВАТЕЛЬ
    # =====================================================

    if user:

        name = user.get("name") or "друг"

        await update.effective_message.reply_text(
            f"С возвращением, {name}! 👋\n\n"
            "Я тебя помню.\n"
            "Продолжаем работать над дисциплиной 💪"
        )

        await show_menu(
            update,
            context
        )

        return

    # =====================================================
    # НОВЫЙ ПОЛЬЗОВАТЕЛЬ
    # =====================================================

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

    await update.effective_message.reply_text(
        "Привет! 👋\n\n"
        "Я Дэн.\n\n"
        "Твой персональный наставник "
        "по дисциплине и развитию.\n\n"
        "Моя задача — помочь тебе "
        "двигаться вперёд маленькими шагами "
        "и превращать их в результат.\n\n"
        "Перед началом хочу немного узнать тебя.\n\n"
        "Готов? 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )