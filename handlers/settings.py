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

from handlers.menu import show_settings

from database.users import (
    get_user,
    update_sleep_settings,
    update_notification_settings,
    delete_user_data,
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


# =========================================================
# ОБРАТНАЯ СВЯЗЬ
# =========================================================

async def start_feedback(update, context):

    query = update.callback_query
    await query.answer()

    feedback_type = query.data

    if feedback_type == "suggest_feature":
        context.user_data["feedback_type"] = "feature"

        text = (
            "💡 <b>Предложить функцию</b>\n\n"
            "Расскажи, какую функцию ты хотел бы увидеть в Дэне.\n\n"
            "Можешь написать идею подробно и, если хочешь, "
            "прикрепить скриншот — так будет проще понять задумку."
        )

    elif feedback_type == "report_problem":
        context.user_data["feedback_type"] = "problem"

        text = (
            "🐞 <b>Сообщить о проблеме</b>\n\n"
            "Расскажи, что произошло и что пошло не так.\n\n"
            "Если можешь — прикрепи скриншот. "
            "Так будет проще разобраться."
        )

    else:
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="feedback_cancel"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel_feedback(update, context):

    query = update.callback_query
    await query.answer()

    context.user_data.pop("feedback_type", None)

    await show_settings(
        update,
        context
    )

# =========================================================
# ПАМЯТЬ ДЭНА
# =========================================================

async def show_dan_memory(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "🧠 <b>Память Дэна</b>\n\n"
        "Дэн использует информацию о тебе, "
        "чтобы лучше понимать твои цели, привычки "
        "и контекст ваших разговоров.\n\n"
        "Ты можешь в любой момент полностью удалить "
        "свои данные.\n\n"
        "После этого Дэн больше не будет ничего о тебе помнить."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🗑️ Удалить мои данные",
                callback_data="delete_my_data"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="back_to_settings"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# =========================================================

async def confirm_delete_user_data(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    text = (
        "⚠️ <b>Удалить всё?</b>\n\n"
        "Будут удалены:\n"
        "• твой профиль\n"
        "• цели\n"
        "• привычки\n"
        "• история чек-инов\n"
        "• прогресс\n"
        "• настройки режима сна и уведомлений\n"
        "• история общения с Дэном\n"
        "• сохранённый контекст Дэна\n\n"
        "<b>После удаления восстановить данные будет нельзя.</b>\n\n"
        "Чтобы снова пользоваться Дэном, "
        "придётся пройти онбординг заново."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🗑️ Да, удалить всё",
                callback_data="confirm_delete_all"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="cancel_delete_data"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ОТМЕНА УДАЛЕНИЯ
# =========================================================

async def cancel_delete_user_data(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    await show_dan_memory(
        update,
        context
    )


# =========================================================
# ОКОНЧАТЕЛЬНОЕ УДАЛЕНИЕ
# =========================================================

async def confirm_delete_all_user_data(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = update.effective_user.id

    # Полностью удаляем данные из БД
    delete_user_data(
        user_id
    )

    # Полностью очищаем временное состояние пользователя
    context.user_data.clear()

    await query.edit_message_text(
        "🗑️ <b>Все твои данные удалены.</b>\n\n"
        "Дэн больше ничего о тебе не помнит.\n\n"
        "Если захочешь вернуться — "
        "начнём знакомство заново. 👋",
        parse_mode="HTML"
    )