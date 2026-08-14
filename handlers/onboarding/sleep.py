from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.users import create_user

from database.users import create_user, get_user

from handlers.day.notifications import setup_day_notifications


async def start_sleep_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["onboarding_step"] = "wake_time"

    await update.effective_message.reply_text(
        "🌅 Отлично. Теперь настроим твой режим дня.\n\n"
        "Во сколько ты обычно просыпаешься? ⏰\n\n"
        "Напиши время, например: <b>08:30</b>",
        parse_mode="HTML"
    )


async def handle_wake_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    wake_time = parse_time(text)

    if wake_time is None:

        await update.message.reply_text(
            "⏰ Не совсем понял время.\n\n"
            "Напиши его в формате <b>08:30</b>.",
            parse_mode="HTML"
        )

        return

    context.user_data["wake_time"] = wake_time
    context.user_data["onboarding_step"] = "sleep_time"

    await update.message.reply_text(
        f"✅ Записал: подъём в <b>{wake_time}</b>.\n\n"
        "Теперь последний вопрос про режим сна. 🌙\n\n"
        "Во сколько ты обычно ложишься спать?\n\n"
        "Например: <b>23:00</b> 😴",
        parse_mode="HTML"
    )


async def handle_sleep_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text.strip()

    sleep_time = parse_time(text)

    if sleep_time is None:

        await update.message.reply_text(
            "⏰ Не совсем понял время.\n\n"
            "Напиши его в формате <b>23:00</b>.",
            parse_mode="HTML"
        )

        return

    context.user_data["sleep_time"] = sleep_time




    setup_day_notifications(
        context,
        update.effective_user.id,
        context.user_data["wake_time"],
        sleep_time
    )


    # =====================================================
    # СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ В БД
    # =====================================================

    create_user(
        user_id=update.effective_user.id,
        name=context.user_data.get("name"),
        age=context.user_data.get("age"),
    )

    saved_user = get_user(
        update.effective_user.id
    )

    print("💾 USER SAVED:", saved_user)

    context.user_data["onboarding_step"] = "finish"

    keyboard = [
        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="open_main_menu"
            )
        ]
    ]

    await update.message.reply_text(
        "🌙 Отлично, записал.\n\n"
        f"🌅 Подъём: <b>{context.user_data['wake_time']}</b>\n"
        f"😴 Сон: <b>{sleep_time}</b>\n\n"
        "Всё готово. 🤝\n\n"
        "Теперь я знаю о тебе достаточно, "
        "чтобы начать работать вместе.\n\n"
        "<b>Ты готов. Поехали. 🚀</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def parse_time(text: str):

    try:
        value = datetime.strptime(
            text,
            "%H:%M"
        )

        return value.strftime(
            "%H:%M"
        )

    except ValueError:

        return None