from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.users import (
    get_user,
    update_sleep_settings,
    update_notification_settings,
)


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
# ЭКРАН УВЕДОМЛЕНИЙ
# =========================================================

async def show_notification_settings(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()

    user = get_user(
        update.effective_user.id
    )

    morning_enabled = (
        user.get("morning_notifications_enabled", True)
        if user
        else True
    )

    evening_enabled = (
        user.get("evening_notifications_enabled", True)
        if user
        else True
    )

    morning_status = (
        "🟢 ВКЛ"
        if morning_enabled
        else
        "🔴 ВЫКЛ"
    )

    evening_status = (
        "🟢 ВКЛ"
        if evening_enabled
        else
        "🔴 ВЫКЛ"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                f"☀️ Утренние: {morning_status}",
                callback_data="toggle_morning_notifications"
            )
        ],

        [
            InlineKeyboardButton(
                f"🌙 Вечерние: {evening_status}",
                callback_data="toggle_evening_notifications"
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
        "🔔 <b>Уведомления</b>\n\n"
        "Здесь можно включить или выключить "
        "автоматические напоминания о чек-инах.\n\n"
        f"☀️ Утренние: <b>{morning_status}</b>\n"
        f"🌙 Вечерние: <b>{evening_status}</b>"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ПЕРЕКЛЮЧЕНИЕ УТРА
# =========================================================

async def toggle_morning_notifications(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user_id = update.effective_user.id

    user = get_user(
        user_id
    )

    current = (
        user.get(
            "morning_notifications_enabled",
            True
        )
        if user
        else True
    )

    update_notification_settings(
        user_id,
        morning_enabled=not current
    )

    await show_notification_settings(
        update,
        context
    )


# =========================================================
# ПЕРЕКЛЮЧЕНИЕ ВЕЧЕРА
# =========================================================

async def toggle_evening_notifications(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user_id = update.effective_user.id

    user = get_user(
        user_id
    )

    current = (
        user.get(
            "evening_notifications_enabled",
            True
        )
        if user
        else True
    )

    update_notification_settings(
        user_id,
        evening_enabled=not current
    )

    await show_notification_settings(
        update,
        context
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