from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.users import update_sleep_settings, get_user


# =========================================================
# ЭКРАН РЕЖИМА ДНЯ
# =========================================================

async def show_sleep_settings(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()


    user = get_user(
        update.effective_user.id
    )


    wake_time = (
        user.get("wake_time")
        if user and user.get("wake_time")
        else "не установлено"
    )

    sleep_time = (
        user.get("sleep_time")
        if user and user.get("sleep_time")
        else "не установлено"
    )


    keyboard = [
        [
            InlineKeyboardButton(
                "🌅 Изменить время подъёма",
                callback_data="change_wake_time"
            )
        ],
        [
            InlineKeyboardButton(
                "🌙 Изменить время сна",
                callback_data="change_sleep_time"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="back_to_settings"
            )
        ],
    ]


    text = (
        "🌙 <b>Режим дня</b>\n\n"
        f"🌅 Подъём: <b>{wake_time}</b>\n"
        f"😴 Сон: <b>{sleep_time}</b>\n\n"
        "Что хочешь изменить?"
    )


    if query:

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )



# =========================================================
# ИЗМЕНИТЬ ПОДЪЁМ
# =========================================================

async def change_wake_time(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    context.user_data[
        "settings_state"
    ] = "wake_time"


    await query.edit_message_text(
        "🌅 <b>Новое время подъёма</b>\n\n"
        "Напиши время в формате:\n"
        "<b>08:30</b>",
        parse_mode="HTML"
    )



# =========================================================
# ИЗМЕНИТЬ СОН
# =========================================================

async def change_sleep_time(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    context.user_data[
        "settings_state"
    ] = "sleep_time"


    await query.edit_message_text(
        "🌙 <b>Новое время сна</b>\n\n"
        "Напиши время в формате:\n"
        "<b>23:00</b>",
        parse_mode="HTML"
    )



# =========================================================
# ПРОВЕРКА ВРЕМЕНИ
# =========================================================

def parse_time(
    text
):

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