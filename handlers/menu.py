from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

async def show_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            "📅 Мой день",
            "🎯 Моя цель",
        ],
        [
            "📊 Мой прогресс",
            "💬 Дэн",
        ],
        [
            "⚙️ Настройки",
            "⭐ PRO",
        ],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.effective_message.reply_text(
        "🏠 Главное меню\n\n"
        "Я здесь. Выбирай, с чего начнём 👇",
        reply_markup=reply_markup
    )


# =========================================================
# ВЫХОД В ГЛАВНОЕ МЕНЮ
# =========================================================

async def go_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()

    # Очищаем только временные состояния интерфейса
    context.user_data.pop("goal_state", None)
    context.user_data.pop("habit_state", None)
    context.user_data.pop("checkin_type", None)
    context.user_data.pop("morning_step", None)

    await show_menu(
        update,
        context
    )


# =========================================================
# PRO
# =========================================================

async def show_pro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.effective_message.reply_text(
        "⭐ <b>PRO</b>\n\n"
        "В PRO будут доступны дополнительные возможности:\n\n"
        "• больше полезных привычек\n"
        "• больше нежелательных привычек\n"
        "• дополнительные цели\n"
        "• расширенная статистика\n"
        "• персонализация Дэна\n\n"
        "🚀 Скоро.",
        parse_mode="HTML"
    )


# =========================================================
# НАСТРОЙКИ
# =========================================================

async def show_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "🌙 Режим сна",
                callback_data="settings_sleep"
            )
        ],
        [
            InlineKeyboardButton(
                "🔔 Уведомления",
                callback_data="settings_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                "🧠 Память Дэна",
                callback_data="settings_memory"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="go_menu"
            )
        ],
    ]

    await update.effective_message.reply_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Выбери, что хочешь изменить:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ОБРАБОТКА ТЕКСТОВЫХ КНОПОК МЕНЮ
# =========================================================

async def menu_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text

    print("🔥 MENU TEXT:", text)

    # -----------------------------------------------------
    # PRO
    # -----------------------------------------------------

    if text == "⭐ PRO":

        await show_pro(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # МОЯ ЦЕЛЬ
    # -----------------------------------------------------

    if text == "🎯 Моя цель":

        from handlers.goal.screen import show_goal

        await show_goal(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # МОЙ ПРОГРЕСС
    # -----------------------------------------------------

    if text == "📊 Мой прогресс":

        from handlers.progress.screen import show_progress

        await show_progress(
            update,
            context
        )

    # -----------------------------------------------------
    # ДЭН
    # -----------------------------------------------------

    if text == "💬 Дэн":

        from handlers.dan import dan_chat

        await dan_chat(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # МОЙ ДЕНЬ
    # -----------------------------------------------------

    if text == "📅 Мой день":

        from handlers.day.screen import show_day

        await show_day(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # НАСТРОЙКИ
    # -----------------------------------------------------

    if text == "⚙️ Настройки":

        await show_settings(
            update,
            context
        )

        return