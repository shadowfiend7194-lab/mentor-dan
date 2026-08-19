from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from database.connection import get_connection

from database.goals import (
    get_main_goal,
    mark_goal_reviewed,
)

from database.habits import (
    get_user_habits,
    mark_habit_reviewed,
)


# =========================================================
# ГЛАВНАЯ ПРОВЕРКА УВЕДОМЛЕНИЙ
# =========================================================

async def check_notifications(
    context
):

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

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_minutes = (
        now.hour * 60
        + now.minute
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


        # =================================================
        # УТРО
        # =================================================

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
                + timedelta(minutes=30)
            )

            notify_minutes = (
                notify.hour * 60
                + notify.minute
            )

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


        # =================================================
        # ВЕЧЕР
        # =================================================

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
                - timedelta(hours=1)
            )

            notify_minutes = (
                notify.hour * 60
                + notify.minute
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


        # =================================================
        # ПРОВЕРКА ЦЕЛИ
        # =================================================

        await check_goal_review(
            context,
            user_id,
            name
        )


        # =================================================
        # ПРОВЕРКА ПРИВЫЧЕК
        # =================================================

        await check_habit_reviews(
            context,
            user_id,
            name
        )


# =========================================================
# ПРОВЕРКА ЦЕЛИ
# =========================================================

async def check_goal_review(
    context,
    user_id,
    name,
):

    goal = get_main_goal(
        user_id
    )

    if not goal:
        return


    created_at = datetime.strptime(
        goal["created_at"],
        "%Y-%m-%d %H:%M:%S"
    )

    now = datetime.now()

    days_since_created = (
        now.date()
        - created_at.date()
    ).days

    last_review = goal.get(
        "last_review_date"
    )

    today_str = now.strftime(
        "%Y-%m-%d"
    )


    if last_review == today_str:
        return


    first_review_due = (
        days_since_created >= 45
        and not last_review
    )


    weekly_review_due = (
        now.weekday() == 6
        and bool(last_review)
    )


    if not (
        first_review_due
        or weekly_review_due
    ):
        return


    keyboard = [

        [
            InlineKeyboardButton(
                "🏆 Да, я достиг",
                callback_data="goal_review_achieved"
            )
        ],

        [
            InlineKeyboardButton(
                "↩️ Пока продолжаю",
                callback_data="goal_review_continue"
            )
        ],

    ]


    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎯 <b>Проверим твою цель</b>\n\n"
            f"«{goal['title']}»\n\n"
            "Ты уже достаточно долго работаешь "
            "в этом направлении.\n\n"
            "Как ты сам считаешь?"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


    mark_goal_reviewed(
        user_id,
        goal["id"],
        today_str
    )


# =========================================================
# УТРЕННЕЕ СООБЩЕНИЕ
# =========================================================

async def send_morning_checkin(
    context,
    user_id,
    name
):

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
        else "evening_notification_sent"
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


# =========================================================
# ПРОВЕРКА ФОРМИРОВАНИЯ / КОНТРОЛЯ ПРИВЫЧЕК
# =========================================================

async def check_habit_reviews(
    context,
    user_id,
    name
):

    habits = get_user_habits(
        user_id
    )

    now = datetime.now()

    today_str = now.strftime(
        "%Y-%m-%d"
    )


    for habit in habits:

        habit_type = habit.get(
            "habit_type"
        )


        # =================================================
        # ХОРОШАЯ ПРИВЫЧКА
        # =================================================

        if habit_type == "good":

            # Уже сформирована
            if habit.get("formed"):
                continue


        # =================================================
        # ПЛОХАЯ ПРИВЫЧКА
        # =================================================

        elif habit_type == "bad":

            # Уже взята под контроль
            if habit.get("controlled"):
                continue


        # =================================================
        # НЕИЗВЕСТНЫЙ ТИП
        # =================================================

        else:

            continue


        created_at_value = habit.get(
            "created_at"
        )

        if not created_at_value:
            continue


        try:

            created_at = datetime.strptime(
                created_at_value,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            continue


        days_since_created = (
            now.date()
            - created_at.date()
        ).days


        last_review = habit.get(
            "last_review_date"
        )


        # Уже спрашивали сегодня
        if last_review == today_str:
            continue


        # =================================================
        # ПЕРВАЯ ПРОВЕРКА — ЧЕРЕЗ 25 ДНЕЙ
        # =================================================

        first_review_due = (
            days_since_created >= 25
            and not last_review
        )


        # =================================================
        # ПОСЛЕДУЮЩИЕ ПРОВЕРКИ — ВОСКРЕСЕНЬЕ
        # =================================================

        weekly_review_due = (
            now.weekday() == 6
            and bool(last_review)
        )


        if not (
            first_review_due
            or weekly_review_due
        ):
            continue


        # =================================================
        # КНОПКИ И ТЕКСТ ДЛЯ ХОРОШЕЙ ПРИВЫЧКИ
        # =================================================

        if habit_type == "good":

            keyboard = [

                [
                    InlineKeyboardButton(
                        "🌱 Да, сформировал",
                        callback_data=(
                            f"habit_review_formed_{habit['id']}"
                        )
                    )
                ],

                [
                    InlineKeyboardButton(
                        "↩️ Пока продолжаю",
                        callback_data=(
                            f"habit_review_continue_{habit['id']}"
                        )
                    )
                ],

            ]


            text = (
                "🌱 <b>Небольшая проверка пути</b>\n\n"
                f"Привычка: «{habit['name']}»\n\n"
                "Ты уже 25 дней держишь этот курс.\n\n"
                "Как ты сам чувствуешь — "
                "эта привычка уже стала "
                "естественной частью твоей жизни?"
            )


        # =================================================
        # КНОПКИ И ТЕКСТ ДЛЯ ПЛОХОЙ ПРИВЫЧКИ
        # =================================================

        else:

            keyboard = [

                [
                    InlineKeyboardButton(
                        "🛡️ Да, держу под контролем",
                        callback_data=(
                            f"bad_habit_controlled_{habit['id']}"
                        )
                    )
                ],

                [
                    InlineKeyboardButton(
                        "↩️ Пока продолжаю",
                        callback_data=(
                            f"bad_habit_continue_{habit['id']}"
                        )
                    )
                ],

            ]


            text = (
                "🛡️ <b>Проверим одну привычку</b>\n\n"
                f"Привычка: «{habit['name']}»\n\n"
                "Ты уже 25 дней работаешь над тем, "
                "чтобы избавиться от этой привычки.\n\n"
                "Как ты сам считаешь — "
                "она уже перестала управлять "
                "твоими решениями?"
            )


        # =================================================
        # ОТПРАВКА
        # =================================================

        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


        mark_habit_reviewed(
            user_id,
            habit["id"],
            today_str
        )