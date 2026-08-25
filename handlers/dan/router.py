import asyncio
import random

from telegram import Update
from telegram.ext import ContextTypes

from services.dan.ai import get_dan_response
from database.dan.conversations import save_dan_message


# =========================================================
# КНОПКИ НИЖНЕГО МЕНЮ
# =========================================================

MENU_BUTTONS = {
    "💬 Дэн",
    "📅 Мой день",
    "📊 Мой прогресс",
    "🎯 Моя цель",
    "⭐ Pro",
    "⚙️ Настройки",
}


# =========================================================
# ОТКРЫТИЕ ВКЛАДКИ ДЭН
# =========================================================

async def open_dan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.callback_query:
        return

    query = update.callback_query

    await query.answer()

    context.user_data["dan_active"] = True

    await query.message.reply_text(
        "🧠 <b>Дэн</b>\n\n"
        "Я твой персональный наставник.\n\n"
        "Здесь ты можешь свободно писать мне "
        "о своих целях, дисциплине, привычках, "
        "состоянии или проблемах.\n\n"
        "Я буду учитывать то, что уже знаю о тебе, "
        "и помогать тебе двигаться вперёд "
        "без лишнего давления.\n\n"
        "Пиши.",
        parse_mode="HTML"
    )


# =========================================================
# ОБРАБОТКА СООБЩЕНИЙ ДЭНУ
# =========================================================

async def dan_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print("🔥🔥🔥 DAN_TEXT_ROUTER ENTERED")

    if not update.message:
        print("❌ NO MESSAGE")
        return False

    user_message = update.message.text

    if not user_message:
        print("❌ EMPTY MESSAGE")
        return True

    # -----------------------------------------------------
    # ЕСЛИ НАЖАТА КНОПКА НИЖНЕГО МЕНЮ
    # -----------------------------------------------------

    if user_message in MENU_BUTTONS:

        print(
            "🚪 DAN CLOSED BY MENU BUTTON:",
            user_message
        )

        close_dan(context)

        # Очень важно:
        # НЕ обрабатываем кнопку как сообщение Дэну.
        # Возвращаем False, чтобы сообщение дальше
        # обработал соответствующий роутер меню.
        return False

    # -----------------------------------------------------
    # ДЭН НЕ АКТИВЕН
    # -----------------------------------------------------

    if not context.user_data.get("dan_active"):

        print("❌ DAN NOT ACTIVE")

        return False

    # -----------------------------------------------------
    # ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЯ
    # -----------------------------------------------------

    user_id = update.effective_user.id

    print("👤 DAN USER ID:", user_id)
    print("💬 DAN MESSAGE:", user_message)

    # -----------------------------------------------------
    # СОХРАНЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    # -----------------------------------------------------

    save_dan_message(
        user_id=user_id,
        role="user",
        message=user_message
    )

    # -----------------------------------------------------
    # ПОЛУЧАЕМ ОТВЕТ ДЭНА
    # -----------------------------------------------------

    print("🧠 CALLING get_dan_response...")

    try:

        response = get_dan_response(
            user_id=user_id,
            user_message=user_message
        )

        print("✅ DAN RESPONSE CREATED")
        print("🤖 RESPONSE:", response)

    except Exception as error:

        print("❌ DAN ERROR:", repr(error))

        await update.message.reply_text(
            "⚠️ Дэн временно не смог сформировать ответ.\n\n"
            "Мы уже разбираемся."
        )

        return True

    # -----------------------------------------------------
    # ПУСТОЙ ОТВЕТ
    # -----------------------------------------------------

    if not response:

        print("❌ EMPTY DAN RESPONSE")

        await update.message.reply_text(
            "🤔 Дэн пока не смог сформировать ответ."
        )

        return True

    # -----------------------------------------------------
    # ОТПРАВЛЯЕМ ОТВЕТ
    # -----------------------------------------------------

    print("📤 SENDING DAN RESPONSE...")

    await update.message.reply_text(
        response
    )

    save_dan_message(
        user_id=user_id,
        role="assistant",
        message=response
    )

    print("✅ DAN RESPONSE SENT")

    return True


# =========================================================
# ВЫХОД ИЗ ДЭНА
# =========================================================

def close_dan(
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.pop(
        "dan_active",
        None
    )

    print("🚪 DAN ACTIVE STATE CLOSED")