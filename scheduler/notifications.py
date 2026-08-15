from datetime import datetime, timedelta

from database.connection import get_connection


# =========================================================
# ГЛАВНАЯ ПРОВЕРКА УВЕДОМЛЕНИЙ
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
            evening_notification_sent,
            morning_notifications_enabled,
            evening_notifications_enabled

        FROM users
        """
    )


    users = cursor.fetchall()

    conn.close()


    now = datetime.now()

    today = now.strftime("%Y-%m-%d")

    current_minutes = (
        now.hour * 60
        +
        now.minute
    )


    for user in users:


        (
            user_id,
            name,
            wake_time,
            sleep_time,
            morning_sent,
            evening_sent,
            morning_enabled,
            evening_enabled
        ) = user



        # ===============================================
        # УТРО
        # ===============================================

        if (
            morning_enabled
            and wake_time
        ):


            wake = datetime.strptime(
                wake_time,
                "%H:%M"
            )


            notify = (
                wake
                +
                timedelta(minutes=30)
            )


            notify_minutes = (
                notify.hour * 60
                +
                notify.minute
            )


            # если время наступило
            # и сегодня еще не отправляли

            if (
                current_minutes >= notify_minutes
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
        # ВЕЧЕР
        # ===============================================


        if (
            evening_enabled
            and sleep_time
        ):


            sleep = datetime.strptime(
                sleep_time,
                "%H:%M"
            )


            notify = (
                sleep
                -
                timedelta(hours=1)
            )


            notify_minutes = (
                notify.hour * 60
                +
                notify.minute
            )


            if (
                current_minutes >= notify_minutes
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
# УТРЕННЕЕ СООБЩЕНИЕ
# =========================================================


async def send_morning_checkin(
    context,
    user_id,
    name
):


    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup
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
                "⏰ Напомнить через час",
                callback_data="delay_morning_checkin"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 В меню",
                callback_data="go_menu"
            )
        ]

    ]


    await context.bot.send_message(

        chat_id=user_id,

        text=(

            f"☀️ Доброе утро, {name}!\n\n"

            "Новый день начинается.\n\n"

            "Перед делами удели минуту себе.\n"

            "Оценим твоё состояние "
            "и начнём день осознанно."

        ),

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )

    )



# =========================================================
# ВЕЧЕРНЕЕ СООБЩЕНИЕ
# =========================================================


async def send_evening_checkin(
    context,
    user_id,
    name
):


    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup
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
                "⏰ Напомнить через час",
                callback_data="delay_evening_checkin"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 В меню",
                callback_data="go_menu"
            )
        ]

    ]


    await context.bot.send_message(

        chat_id=user_id,

        text=(

            f"🌙 Добрый вечер, {name}!\n\n"

            "День подходит к концу.\n\n"

            "Самое время остановиться "
            "и посмотреть, как он прошёл."

        ),

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )

    )



# =========================================================
# СОХРАНЕНИЕ ОТПРАВКИ
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