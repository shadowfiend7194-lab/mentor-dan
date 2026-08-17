from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.users import get_user
from database.connection import get_connection
from database.events import get_user_events


# =========================================================
# ИСТОРИЯ ПУТИ
# =========================================================

async def show_history(
    update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:
        await query.answer()

    user_id = update.effective_user.id

    user = get_user(user_id)

    # =====================================================
    # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН
    # =====================================================

    if not user:

        text = (
            "🛤️ <b>Твой путь</b>\n\n"
            "Пока не удалось найти данные о твоём пути."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data="back_to_progress"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # =====================================================
    # ДНИ С ДЭНОМ
    # =====================================================

    created_at = user.get("created_at")

    if created_at:

        try:

            start_date = datetime.strptime(
                created_at,
                "%Y-%m-%d %H:%M:%S"
            )

            days_with_dan = (
                datetime.now().date()
                - start_date.date()
            ).days + 1

        except ValueError:

            days_with_dan = 1

    else:

        days_with_dan = 1

    # =====================================================
    # КОЛИЧЕСТВО ЧЕК-ИНОВ
    # =====================================================

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM checkin_history
        WHERE
            user_id = ?
            AND completed = 1
        """,
        (
            user_id,
        )
    )

    result = cursor.fetchone()

    checkin_count = (
        result[0]
        if result
        else 0
    )

    conn.close()

    # =====================================================
    # ИСТОРИЯ СОБЫТИЙ
    # =====================================================

    events = get_user_events(
        user_id,
        limit=7
    )

    # =====================================================
    # ТЕКСТ
    # =====================================================

    text = (
        "🛤️ <b>Твой путь</b>\n\n"

        f"👣 Ты с Дэном уже "
        f"<b>{days_with_dan} "
        f"{get_day_word(days_with_dan)}</b>\n\n"

        "📅 <b>Начало пути:</b>\n"
        f"{format_date(created_at)}\n\n"

        "🔥 <b>Твои результаты:</b>\n\n"

        f"✅ Чек-инов пройдено: "
        f"<b>{checkin_count}</b>\n\n"

        "📖 <b>История пути:</b>\n\n"
    )

    # =====================================================
    # ЕСЛИ СОБЫТИЯ ЕСТЬ
    # =====================================================

    if events:

        for event in events:

            event_type = event[0]
            title = event[1]
            description = event[2]
            created_at_event = event[3]

            icon = {
                "start": "🌱",
                "first_morning_checkin": "☀️",
                "first_evening_checkin": "🌙",
                "rhythm": "🔥",
                "comeback": "👊",
                "achievement": "🏆",
            }.get(
                event_type,
                "⭐"
            )

            text += (
                f"{icon} <b>{title}</b>\n"
                f"{description}\n"
                f"<i>{format_event_date(created_at_event)}</i>\n\n"
            )

    # =====================================================
    # ЕСЛИ СОБЫТИЙ НЕТ
    # =====================================================

    else:

        text += (
            "Путь только начинается.\n"
            "Здесь будут появляться важные моменты "
            "твоего движения с Дэном 👣"
        )

    # =====================================================
    # КНОПКА НАЗАД
    # =====================================================

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="back_to_progress"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ДЕНЬ / ДНЯ / ДНЕЙ
# =========================================================

def get_day_word(
    number
):

    number = number % 100

    if 11 <= number <= 14:
        return "дней"

    number = number % 10

    if number == 1:
        return "день"

    if 2 <= number <= 4:
        return "дня"

    return "дней"


# =========================================================
# ФОРМАТ ДАТЫ НАЧАЛА ПУТИ
# =========================================================

def format_date(
    value
):

    if not value:
        return "Дата неизвестна"

    try:

        date = datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S"
        )

        return date.strftime(
            "%d.%m.%Y"
        )

    except ValueError:

        return value


# =========================================================
# ФОРМАТ ДАТЫ СОБЫТИЯ
# =========================================================

def format_event_date(
    value
):

    if not value:
        return ""

    try:

        date = datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S"
        )

        return date.strftime(
            "%d.%m.%Y"
        )

    except ValueError:

        return value