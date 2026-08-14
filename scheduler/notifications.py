from datetime import datetime, timedelta

from database.connection import get_connection


# =========================================================
# ПРОВЕРКА УТРЕННИХ И ВЕЧЕРНИХ УВЕДОМЛЕНИЙ
# =========================================================

async def check_notifications(context):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            user_id,
            name,
            wake_time,
            sleep_time,
            morning_notification_sent,
            evening_notification_sent

        FROM users
        """
    )


    users = cursor.fetchall()


    conn.close()


    now = datetime.now()


    for user in users:

        (
            user_id,
            name,
            wake_time,
            sleep_time,
            morning_sent,
            evening_sent
        ) = user


        # ===============================================
        # УТРЕННИЙ ЧЕК-ИН
        # ===============================================

        if wake_time:

            wake = datetime.strptime(
                wake_time,
                "%H:%M"
            )


            notify_time = (
                wake
                + timedelta(minutes=30)
            )


            current_time = now.strftime(
                "%H:%M"
            )


            target_time = notify_time.strftime(
                "%H:%M"
            )


            today = now.strftime(
                "%Y-%m-%d"
            )


            if (
                current_time == target_time
                and morning_sent != today
            ):

                await send_morning_checkin(
                    context,
                    user_id,
                    name
                )

                save_notification(
                    user_id,
                    "morning"
                )


        # ===============================================
        # ВЕЧЕРНИЙ ЧЕК-ИН
        # ===============================================

        if sleep_time:

            sleep = datetime.strptime(
                sleep_time,
                "%H:%M"
            )


            notify_time = (
                sleep
                - timedelta(hours=1)
            )


            current_time = now.strftime(
                "%H:%M"
            )


            target_time = notify_time.strftime(
                "%H:%M"
            )


            today = now.strftime(
                "%Y-%m-%d"
            )


            if (
                current_time == target_time
                and evening_sent != today
            ):

                await send_evening_checkin(
                    context,
                    user_id,
                    name
                )

                save_notification(
                    user_id,
                    "evening"
                )



# =========================================================
# ОТПРАВКА
# =========================================================


async def send_morning_checkin(
    context,
    user_id,
    name
):

    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )


    keyboard = [
        [
            InlineKeyboardButton(
                "🌅 Пройти утренний чек-ин",
                callback_data="day_morning"
            )
        ],
        [
            InlineKeyboardButton(
                "⏳ Позже",
                callback_data="morning_later"
            )
        ],
    ]


    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"☀️ Доброе утро, {name}!\n\n"
            "Новый день начинается.\n\n"
            "Перед тем как погрузиться в дела — "
            "оцени своё состояние.\n\n"
            "Это займёт меньше минуты, "
            "но поможет лучше понимать себя.\n\n"
            "Готов пройти утренний чек-ин?"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def send_evening_checkin(
    context,
    user_id,
    name
):

    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )


    keyboard = [
        [
            InlineKeyboardButton(
                "🌙 Пройти вечерний чек-ин",
                callback_data="day_evening"
            )
        ],
        [
            InlineKeyboardButton(
                "⏳ Позже",
                callback_data="evening_later"
            )
        ],
    ]


    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"🌙 Добрый вечер, {name}!\n\n"
            "День завершён.\n\n"
            "Самое время немного остановиться "
            "и посмотреть назад: "
            "что получилось, что было сложно "
            "и какой вывод можно забрать с собой.\n\n"
            "Займёт всего пару минут."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# =========================================================
# СОХРАНЕНИЕ ФАКТА ОТПРАВКИ
# =========================================================


def save_notification(
    user_id,
    notification_type
):

    conn = get_connection()
    cursor = conn.cursor()


    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    field = (
        "morning_notification_sent"
        if notification_type == "morning"
        else
        "evening_notification_sent"
    )


    cursor.execute(
        f"""
        UPDATE users

        SET {field} = ?

        WHERE user_id = ?
        """,
        (
            today,
            user_id
        )
    )


    conn.commit()
    conn.close()