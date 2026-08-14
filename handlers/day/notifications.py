from datetime import datetime, timedelta, time

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from database.users import get_user


# =====================================================
# УТРЕННИЙ ЧЕК-ИН
# =====================================================

async def send_morning_checkin(
    context
):

    user_id = context.job.chat_id

    user = get_user(user_id)

    name = (
        user["name"]
        if user
        else "друг"
    )


    keyboard = [
        [
            InlineKeyboardButton(
                "🌅 Утренний чек-ин",
                callback_data="day_morning"
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
            f"🌅 Доброе утро, {name}!\n\n"
            "Новый день начинается.\n"
            "Давай уделим минуту себе и оценим состояние.\n\n"
            "Готов пройти утренний чек-ин?"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# =====================================================
# ВЕЧЕРНИЙ ЧЕК-ИН
# =====================================================

async def send_evening_checkin(
    context
):

    user_id = context.job.chat_id

    user = get_user(user_id)

    name = (
        user["name"]
        if user
        else "друг"
    )


    keyboard = [
        [
            InlineKeyboardButton(
                "🌙 Вечерний чек-ин",
                callback_data="day_evening"
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
            f"🌙 {name}, скоро время отдыха.\n\n"
            "Перед сном удели минуту себе.\n"
            "Оцени день и зафиксируй результат."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# =====================================================
# СОЗДАНИЕ УВЕДОМЛЕНИЙ
# =====================================================

def setup_day_notifications(
    context,
    user_id,
    wake_time,
    sleep_time
):

    scheduler = context.job_queue


    wake = datetime.strptime(
        wake_time,
        "%H:%M"
    )


    morning_time = (
        wake + timedelta(minutes=30)
    ).time()



    sleep = datetime.strptime(
        sleep_time,
        "%H:%M"
    )


    evening_time = (
        sleep - timedelta(hours=1)
    ).time()



    scheduler.run_daily(
        send_morning_checkin,
        morning_time,
        chat_id=user_id,
        name=f"morning_{user_id}"
    )


    scheduler.run_daily(
        send_evening_checkin,
        evening_time,
        chat_id=user_id,
        name=f"evening_{user_id}"
    )