from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from telegram.ext import ContextTypes

from database.users import update_checkin_date
from database.checkin_history import save_checkin_status
from database.checkins import save_checkin
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

        # =================================================
        # 7–10 — БЕЗ ДОПОЛНИТЕЛЬНЫХ ВОПРОСОВ
        # =================================================

        if score >= 7:

            await finish_evening(
                update,
                context
            )

            return True

        # =================================================
        # 4–6 — ОДИН ВОПРОС
        # =================================================

        elif score >= 4:

            context.user_data[
                "evening_step"
            ] = "normal_reflection"

            await update.message.reply_text(
                "💭 Что сегодня сильнее всего повлияло "
                "на твою оценку дня?",
                reply_markup=ReplyKeyboardRemove()
            )

            return True

        # =================================================
        # 1–3 — ПЕРВЫЙ ВОПРОС
        # =================================================

        else:

            context.user_data[
                "evening_step"
            ] = "low_reason"

            await update.message.reply_text(
                "🌙 Что сегодня больше всего выбило "
                "день из колеи?",
                reply_markup=ReplyKeyboardRemove()
            )

            return True

    # -----------------------------------------------------
    # 4–6 — ЕДИНСТВЕННЫЙ ВОПРОС
    # -----------------------------------------------------

    if step == "normal_reflection":

        context.user_data[
            "evening_positive"
        ] = update.message.text

        await finish_evening(
            update,
            context
        )

        return True

    # -----------------------------------------------------
    # 1–3 — ПЕРВЫЙ ВОПРОС
    # -----------------------------------------------------

    if step == "low_reason":

        context.user_data[
            "evening_problem"
        ] = update.message.text

        context.user_data[
            "evening_step"
        ] = "low_tomorrow"

        await update.message.reply_text(
            "🌅 А что завтра можно сделать иначе, "
            "чтобы день прошёл хотя бы немного лучше?"
        )

        return True

    # -----------------------------------------------------
    # 1–3 — ВТОРОЙ ВОПРОС
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
            "строится дисциплина. 👣\n\n"
            "Сладких снов 🌙"
        )

    elif score >= 5:

        result = (
            "👌 Хорошо.\n\n"
            "Ты остановился и посмотрел "
            "на свой день.\n\n"
            "Именно так появляется стабильность. 💪\n\n"
            "Продолжаем завтра. Спокойной ночи!🌙"
        )

    else:

        result = (
            "🤝 Спасибо, что честно разобрал "
            "этот день.\n\n"
            "Плохой день — это не провал.\n\n"
            "Главное — выбрать один шаг "
            "и сделать его завтра. 👣\n\n"
            "А сейчас востанавливайся. Спокойной ночи!🌙"
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

    save_checkin(
        user_id=update.effective_user.id,
        evening_score=context.user_data.get("evening_score"),
        evening_problem=context.user_data.get("evening_problem"),
        evening_positive=context.user_data.get("evening_positive"),
        evening_improve=context.user_data.get("evening_improve"),
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