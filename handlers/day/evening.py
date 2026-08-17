from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from telegram.ext import ContextTypes

from database.users import update_checkin_date
from database.checkin_history import save_checkin_status
from database.events import add_event

from database.achievements import (
    check_and_award_achievements,
)

# =========================================================
# СТАРТ ВЕЧЕРНЕГО ЧЕК-ИНА
# =========================================================

async def start_evening_checkin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.pop(
        "checkin_type",
        None
    )

    context.user_data.pop(
        "evening_step",
        None
    )

    context.user_data["checkin_type"] = "evening"
    context.user_data["evening_step"] = "score"

    await send_scale(
        update,
        (
            "🌙 <b>Вечерний чек-ин</b>\n\n"
            "День подходит к концу.\n"
            "Давай на минуту остановимся "
            "и посмотрим, как он прошёл. 👀\n\n"
            "Как ты оцениваешь сегодняшний день "
            "от 1 до 10?"
        )
    )


# =========================================================
# ОБРАБОТКА ВСЕХ ТЕКСТОВ ВЕЧЕРНЕГО ЧЕК-ИНА
# =========================================================

async def handle_evening_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    step = context.user_data.get(
        "evening_step"
    )

    # -----------------------------------------------------
    # ОЦЕНКА ДНЯ
    # -----------------------------------------------------

    if step == "score":

        text = update.message.text

        if text not in [
            str(i)
            for i in range(1, 11)
        ]:
            return False

        score = int(text)

        context.user_data[
            "evening_score"
        ] = score

        # Ветка 8-10

        if score >= 8:

            context.user_data[
                "evening_step"
            ] = "high_reflection"

            await update.message.reply_text(
                "🔥 Хороший день.\n\n"
                "Что сегодня получилось лучше всего?\n\n"
                "Напиши своими словами.",
                reply_markup=ReplyKeyboardRemove()
            )

        # Ветка 5-7

        elif score >= 5:

            context.user_data[
                "evening_step"
            ] = "normal_positive"

            await update.message.reply_text(
                "👍 Нормальный день.\n\n"
                "Что сегодня получилось хорошо? 💭",
                reply_markup=ReplyKeyboardRemove()
            )

        # Ветка 1-4

        else:

            context.user_data[
                "evening_step"
            ] = "low_reason"

            await update.message.reply_text(
                "🫂 Сегодня день, похоже, "
                "был непростым.\n\n"
                "Что больше всего помешало тебе "
                "провести его так, как хотелось?",
                reply_markup=ReplyKeyboardRemove()
            )

        return True

    # -----------------------------------------------------
    # ХОРОШИЙ ДЕНЬ
    # -----------------------------------------------------

    if step == "high_reflection":

        context.user_data[
            "evening_positive"
        ] = update.message.text

        await finish_evening(
            update,
            context
        )

        return True

    # -----------------------------------------------------
    # СРЕДНИЙ ДЕНЬ — ПЕРВЫЙ ВОПРОС
    # -----------------------------------------------------

    if step == "normal_positive":

        context.user_data[
            "evening_positive"
        ] = update.message.text

        context.user_data[
            "evening_step"
        ] = "normal_improve"

        await update.message.reply_text(
            "🚀 А что завтра можно сделать "
            "немного лучше?\n\n"
            "Достаточно одного небольшого шага."
        )

        return True

    # -----------------------------------------------------
    # СРЕДНИЙ ДЕНЬ — ВТОРОЙ ВОПРОС
    # -----------------------------------------------------

    if step == "normal_improve":

        context.user_data[
            "evening_improve"
        ] = update.message.text

        await finish_evening(
            update,
            context
        )

        return True

    # -----------------------------------------------------
    # ПЛОХОЙ ДЕНЬ — ПРИЧИНА
    # -----------------------------------------------------

    if step == "low_reason":

        context.user_data[
            "evening_problem"
        ] = update.message.text

        context.user_data[
            "evening_step"
        ] = "low_good"

        await update.message.reply_text(
            "💭 Несмотря на всё это,\n"
            "что сегодня всё-таки получилось?\n\n"
            "Даже что-то совсем небольшое."
        )

        return True

    # -----------------------------------------------------
    # ПЛОХОЙ ДЕНЬ — ЧТО ПОЛУЧИЛОСЬ
    # -----------------------------------------------------

    if step == "low_good":

        context.user_data[
            "evening_positive"
        ] = update.message.text

        context.user_data[
            "evening_step"
        ] = "low_tomorrow"

        await update.message.reply_text(
            "🌅 И последнее.\n\n"
            "Что ты хочешь изменить завтра,\n"
            "чтобы день прошёл немного лучше?"
        )

        return True

    # -----------------------------------------------------
    # ПЛОХОЙ ДЕНЬ — ШАГ НА ЗАВТРА
    # -----------------------------------------------------

    if step == "low_tomorrow":

        context.user_data[
            "evening_improve"
        ] = update.message.text

        await finish_evening(
            update,
            context
        )

        return True

    return False


# =========================================================
# ФИНАЛ
# =========================================================

async def finish_evening(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    score = context.user_data.get(
        "evening_score",
        5
    )

    if score >= 8:

        result = (
            "💪 Отлично.\n\n"
            "Зафиксировал твой день.\n\n"
            "Не останавливайся на этом — "
            "так держать и завтра! 🔥\n\n"
            "Именно из таких дней "
            "строится дисциплина. 👣"
        )

    elif score >= 5:

        result = (
            "👌 Хорошо.\n\n"
            "Ты остановился и посмотрел "
            "на свой день.\n\n"
            "Именно так появляется стабильность. 💪\n\n"
            "Продолжаем завтра. 👊"
        )

    else:

        result = (
            "🤝 Спасибо, что честно разобрал "
            "этот день.\n\n"
            "Плохой день — это не провал.\n\n"
            "Главное — выбрать один шаг "
            "и сделать его завтра. 👣\n\n"
            "Ты справишься. 🔥"
        )

    await update.message.reply_text(
        result,
        reply_markup=ReplyKeyboardRemove()
    )

    # -----------------------------------------------------
    # СОХРАНЯЕМ ФАКТ ВЕЧЕРНЕГО ЧЕК-ИНА
    # -----------------------------------------------------

    update_checkin_date(
        update.effective_user.id,
        "evening"
    )


    save_checkin_status(
        user_id=update.effective_user.id,
        checkin_type="evening",
        completed=1
    )


    await check_and_award_achievements(
         update,
        context
    )

    # -----------------------------------------------------
    # СОБЫТИЕ ИСТОРИИ ПУТИ
    # -----------------------------------------------------

    add_event(
        user_id=update.effective_user.id,
        event_type="first_evening_checkin",
        title="Первый вечерний чек-ин",
        description=(
            "Впервые остановился и подвёл итог дня."
        )
    )

    # -----------------------------------------------------
    # ОЧИЩАЕМ СОСТОЯНИЕ
    # -----------------------------------------------------

    clear_evening_state(
        context
    )

    # -----------------------------------------------------
    # ВОЗВРАЩАЕМ ГЛАВНОЕ МЕНЮ
    # -----------------------------------------------------

    from handlers.menu import show_menu

    import asyncio

    await asyncio.sleep(1)

    await show_menu(
        update,
        context
    )


# =========================================================
# ШКАЛА
# =========================================================

async def send_scale(
    update: Update,
    text: str
):

    keyboard = [
        ["1", "2", "3", "4", "5"],
        ["6", "7", "8", "9", "10"],
    ]

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# =========================================================
# ОЧИСТКА
# =========================================================

def clear_evening_state(
    context: ContextTypes.DEFAULT_TYPE
):

    for key in [
        "checkin_type",
        "evening_step",
        "evening_score",
        "evening_problem",
        "evening_positive",
        "evening_improve",
    ]:

        context.user_data.pop(
            key,
            None
        )