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

    # =====================================================
    # ТЕСТОВЫЙ РЕЖИМ
    # =====================================================

    test_reset = context.user_data.get(
        "reset_onboarding_test"
    )

    if test_reset:

        context.user_data.pop(
            "reset_onboarding_test",
            None
        )

        context.user_data[
            "onboarding_step"
        ] = None

        print(
            "🧪 TEST MODE: запускаем онбординг заново"
        )

    # =====================================================
    # СТАРЫЙ ПОЛЬЗОВАТЕЛЬ
    # =====================================================

    elif user:

        # Существующий пользователь всегда считается прошедшим онбординг.
        # Это защищает от старого зависшего onboarding_step, который мог
        # перехватить кнопку «🎯 Моя цель» как текст новой цели.
        context.user_data["onboarding_step"] = "completed"

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
    # НОВЫЙ / ТЕСТОВЫЙ ПОЛЬЗОВАТЕЛЬ
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
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )