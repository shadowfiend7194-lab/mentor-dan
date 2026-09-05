from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

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

from handlers.progress.weekly_report import generate_weekly_report
from database.weekly_reports import save_weekly_report
from services.subscription import user_has_pro
from services.dan.pro_weekly_report import build_weekly_report

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

    now = datetime.now(
        ZoneInfo("Europe/Moscow")
    )

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

            # Окно утреннего уведомления:
            # отправляем только в течение часа после времени подъёма

            morning_window_end = (
                notify_minutes
                + 60
            )


            if (
                notify_minutes <= current_minutes <= morning_window_end
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
        
        await check_weekly_report(
            context,
            user_id
        )

# =========================================================
# ПРОВЕРКА ЦЕЛИ
# =========================================================

async def check_goal_review(
    context,
    user_id,
    name,
):

    from services.subscription import (
        is_pro,
    )

    # =====================================================
    # PRO
    # =====================================================

    if is_pro(user_id):

        from services.dan.pro_progress import (
            calculate_goal_progress,
        )

        from database.goals import (
            get_main_goal,
            mark_goal_reviewed,
        )

        goal = get_main_goal(
            user_id
        )

        if not goal:
            return

        today_str = (
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )

        last_review = goal.get(
            "last_review_date"
        )

        if last_review == today_str:
            return

        try:

            progress = calculate_goal_progress(
                user_id,
                goal["id"],
            )

        except Exception as error:

            print(
                f"[GOAL PROGRESS] "
                f"Ошибка расчёта цели: {error}"
            )

            return

        if not progress:
            return

        # -------------------------------------------------
        # PRO НЕ СПРАШИВАЕТ ПРО ЦЕЛЬ,
        # ПОКА МАТЕМАТИКА НЕ ГОТОВА
        # -------------------------------------------------

        if not progress.get(
            "goal_ready"
        ):

            return

        keyboard = [

            [
                InlineKeyboardButton(
                    "🏆 Да, я достиг",
                    callback_data=(
                        "goal_review_achieved"
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    "↩️ Пока продолжаю",
                    callback_data=(
                        "goal_review_continue"
                    )
                )
            ],

        ]

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎯 <b>Похоже, ты серьёзно "
                "продвинулся.</b>\n\n"
                f"«{goal['title']}»\n\n"
                f"Стабильность связанных привычек: "
                f"<b>{progress.get('average_stability', 0)}%</b>\n"
                f"Прогресс по цели: "
                f"<b>{progress.get('goal_progress', 0)}%</b>\n\n"
                "Ты уже достаточно долго работаешь "
                "в этом направлении.\n\n"
                "Как ты сам считаешь — "
                "цель достигнута?"
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

        return

    # =====================================================
    # FREE
    # =====================================================
    #
    # Старую механику FREE не меняем.
    #
    # =====================================================

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

    today_str = (
        now.strftime(
            "%Y-%m-%d"
        )
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
                callback_data=(
                    "goal_review_achieved"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "↩️ Пока продолжаю",
                callback_data=(
                    "goal_review_continue"
                )
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

    from services.subscription import (
        is_pro,
    )

    habits = get_user_habits(
        user_id
    )

    now = datetime.now()

    today_str = (
        now.strftime(
            "%Y-%m-%d"
        )
    )

    # =====================================================
    # PRO-МАТЕМАТИКА
    # =====================================================

    pro_active = False

    try:

        pro_active = bool(
            is_pro(user_id)
        )

    except Exception:

        pro_active = False

    # =====================================================
    # ПРОХОДИМ ПО ПРИВЫЧКАМ
    # =====================================================

    for habit in habits:

        habit_type = habit.get(
            "habit_type"
        )

        # -------------------------------------------------
        # GOOD
        # -------------------------------------------------

        if habit_type == "good":

            if habit.get(
                "formed"
            ):

                continue

        # -------------------------------------------------
        # BAD
        # -------------------------------------------------

        elif habit_type == "bad":

            if habit.get(
                "controlled"
            ):

                continue

        # -------------------------------------------------
        # НЕИЗВЕСТНЫЙ ТИП
        # -------------------------------------------------

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

        # -------------------------------------------------
        # НЕ СПРАШИВАЕМ ДВАЖДЫ В ОДИН ДЕНЬ
        # -------------------------------------------------

        if last_review == today_str:

            continue

        # =================================================
        # PRO
        # =================================================

        if pro_active:

            from services.dan.pro_progress import (
                calculate_habit_statistics,
            )

            try:

                statistics = (
                    calculate_habit_statistics(
                        habit
                    )
                )

            except Exception as error:

                print(
                    f"[HABIT PROGRESS] "
                    f"Ошибка расчёта "
                    f"привычки {habit.get('id')}: "
                    f"{error}"
                )

                continue

            # -------------------------------------------------
            # PRO-ПРАВИЛО
            # -------------------------------------------------
            #
            # Неважно, сколько просто прошло дней.
            #
            # Дэн ждёт, пока привычка:
            #
            # 1. пройдёт индивидуальный срок;
            # 2. наберёт достаточную стабильность.
            #
            # -------------------------------------------------

            if not statistics.get(
                "formation_ready"
            ):

                continue

            # -------------------------------------------------
            # GOOD
            # -------------------------------------------------

            if habit_type == "good":

                keyboard = [

                    [
                        InlineKeyboardButton(
                            "🌳 Да, сформировал",
                            callback_data=(
                                f"habit_review_formed_"
                                f"{habit['id']}"
                            )
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "↩️ Пока продолжаю",
                            callback_data=(
                                f"habit_review_continue_"
                                f"{habit['id']}"
                            )
                        )
                    ],

                ]

                text = (
                    "🌱 <b>Пора проверить привычку</b>\n\n"
                    f"«{habit['name']}»\n\n"
                    f"Твоя текущая стабильность: "
                    f"<b>{statistics.get('adjusted_stability', 0)}%</b>\n"
                    f"Сложность: "
                    f"<b>{statistics.get('difficulty', 3)}/5</b>\n\n"
                    "По расчётам Дэна, ты уже достаточно "
                    "долго и стабильно работаешь над ней.\n\n"
                    "Как тебе кажется — эта привычка "
                    "уже стала естественной частью "
                    "твоего ритма?"
                )

            # -------------------------------------------------
            # BAD
            # -------------------------------------------------

            else:

                keyboard = [

                    [
                        InlineKeyboardButton(
                            "🛡️ Да, держу под контролем",
                            callback_data=(
                                f"bad_habit_controlled_"
                                f"{habit['id']}"
                            )
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "↩️ Пока продолжаю",
                            callback_data=(
                                f"bad_habit_continue_"
                                f"{habit['id']}"
                            )
                        )
                    ],

                ]

                text = (
                    "🛡️ <b>Пора проверить результат</b>\n\n"
                    f"«{habit['name']}»\n\n"
                    f"Твоя текущая стабильность: "
                    f"<b>{statistics.get('adjusted_stability', 0)}%</b>\n"
                    f"Сложность: "
                    f"<b>{statistics.get('difficulty', 3)}/5</b>\n\n"
                    "По расчётам Дэна, ты уже достаточно "
                    "долго удерживаешь новое поведение.\n\n"
                    "Как тебе кажется — эта привычка "
                    "уже действительно под контролем?"
                )

            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

            from database.habits import (
                mark_habit_reviewed,
            )

            mark_habit_reviewed(
                user_id,
                habit["id"],
                today_str
            )

            continue

        # =================================================
        # FREE
        # =================================================
        #
        # Старую систему не меняем.
        #
        # Первая проверка через 25 дней,
        # дальше по воскресеньям.
        #
        # =================================================

        first_review_due = (
            days_since_created >= 25
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

            continue

        # -------------------------------------------------
        # GOOD
        # -------------------------------------------------

        if habit_type == "good":

            keyboard = [

                [
                    InlineKeyboardButton(
                        "🌱 Да, сформировал",
                        callback_data=(
                            f"habit_review_formed_"
                            f"{habit['id']}"
                        )
                    )
                ],

                [
                    InlineKeyboardButton(
                        "↩️ Пока продолжаю",
                        callback_data=(
                            f"habit_review_continue_"
                            f"{habit['id']}"
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

        # -------------------------------------------------
        # BAD
        # -------------------------------------------------

        else:

            keyboard = [

                [
                    InlineKeyboardButton(
                        "🛡️ Да, держу под контролем",
                        callback_data=(
                            f"bad_habit_controlled_"
                            f"{habit['id']}"
                        )
                    )
                ],

                [
                    InlineKeyboardButton(
                        "↩️ Пока продолжаю",
                        callback_data=(
                            f"bad_habit_continue_"
                            f"{habit['id']}"
                        )
                    )
                ],

            ]

            text = (
                "🛡️ <b>Проверим твой прогресс</b>\n\n"
                f"Привычка: «{habit['name']}»\n\n"
                "Ты уже какое-то время работаешь "
                "над этим поведением.\n\n"
                "Как ты сам считаешь — "
                "она уже под контролем?"
            )

        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        from database.habits import (
            mark_habit_reviewed,
        )

        mark_habit_reviewed(
            user_id,
            habit["id"],
            today_str
        )


async def check_weekly_report(context, user_id):
    """Отправляет PRO-анализ строго в воскресенье в 21:00 по Москве."""
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    if now.weekday() != 6 or now.hour != 21:
        return
    if not user_has_pro(user_id):
        return

    today = now.date().isoformat()
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT weekly_report_sent FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone(); conn.close()
    if row and row[0] == today:
        return

    text, chart = build_weekly_report(user_id, today=now.date())
    if not text:
        return
    save_weekly_report(user_id, text)

    if chart:
        await context.bot.send_photo(chat_id=user_id, photo=chart)
    await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")

    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("UPDATE users SET weekly_report_sent = ? WHERE user_id = ?", (today, user_id))
    conn.commit(); conn.close()
