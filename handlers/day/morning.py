from telegram import (
    Update,
    ReplyKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.checkins import save_checkin
from database.users import update_checkin_date


# =========================================================
# УТРЕННИЙ ЧЕК-ИН
# =========================================================

async def morning_checkin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # Очищаем только состояние чек-ина,
    # не трогая остальные данные пользователя.
    context.user_data.pop(
        "checkin_type",
        None
    )

    context.user_data.pop(
        "morning_step",
        None
    )

    context.user_data["checkin_type"] = "morning"
    context.user_data["morning_step"] = "energy"

    await send_scale(
        update,
        (
            "☀️ <b>Утренний чек-ин</b>\n\n"
            "Начнём с энергии.\n\n"
            "⚡ Сколько у тебя сейчас сил?\n\n"
            "1 — совсем нет сил\n"
            "10 — энергии очень много."
        )
    )


# =========================================================
# ОБРАБОТКА ОТВЕТОВ
# =========================================================

async def morning_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text

    if text not in [
        str(number)
        for number in range(1, 11)
    ]:
        return

    score = int(text)

    step = context.user_data.get(
        "morning_step"
    )

    # -----------------------------------------------------
    # ЭНЕРГИЯ
    # -----------------------------------------------------

    if step == "energy":

        context.user_data["energy"] = score

        context.user_data[
            "morning_step"
        ] = "sleep"

        await send_scale(
            update,
            (
                "😴 <b>Сон</b>\n\n"
                "Насколько хорошо ты выспался?\n\n"
                "1 — ужасно\n"
                "10 — полностью восстановился."
            )
        )

        return

    # -----------------------------------------------------
    # СОН
    # -----------------------------------------------------

    if step == "sleep":

        context.user_data["sleep"] = score

        context.user_data[
            "morning_step"
        ] = "mood"

        await send_scale(
            update,
            (
                "🙂 <b>Настрой</b>\n\n"
                "Какое у тебя внутреннее состояние?\n\n"
                "1 — очень плохое\n"
                "10 — отличный настрой."
            )
        )

        return

    # -----------------------------------------------------
    # НАСТРОЙ
    # -----------------------------------------------------

    if step == "mood":

        context.user_data["mood"] = score

        context.user_data[
            "morning_step"
        ] = "stress"

        await send_scale(
            update,
            (
                "🧠 <b>Стресс</b>\n\n"
                "Какой уровень напряжения сейчас?\n\n"
                "1 — спокойно\n"
                "10 — очень высокий стресс."
            )
        )

        return

    # -----------------------------------------------------
    # СТРЕСС — ЗАВЕРШЕНИЕ
    # -----------------------------------------------------

    if step == "stress":

        energy = context.user_data.get(
            "energy",
            5
        )

        sleep = context.user_data.get(
            "sleep",
            5
        )

        mood = context.user_data.get(
            "mood",
            5
        )

        save_checkin(
            user_id=update.effective_user.id,
            morning_energy=energy,
            morning_sleep=sleep,
            morning_mood=mood,
            morning_stress=score,
        )
        
        update_checkin_date(
            update.effective_user.id,
            "morning"
        )
        
        # -------------------------------------------------
        # КОРОТКИЙ АНАЛИЗ
        # -------------------------------------------------

        if energy <= 4 and sleep <= 4:

            result = (
                "🫂 Сегодня лучше идти спокойно.\n\n"
                "Ресурс ограничен. Не пытайся "
                "закрыть всё сразу."
            )

        elif energy >= 8 and sleep >= 8:

            result = (
                "🔥 Отличный старт.\n\n"
                "Сегодня хороший момент "
                "для важной задачи."
            )

        else:

            result = (
                "👍 Нормальный старт дня.\n\n"
                "Главное — сохранить ритм."
            )

        # -------------------------------------------------
        # АНАЛИЗ
        # -------------------------------------------------

        await update.message.reply_text(
            result
        )

        # -------------------------------------------------
        # ОЧИЩАЕМ СОСТОЯНИЕ
        # -------------------------------------------------

        clear_morning_state(
            context
        )

        # -------------------------------------------------
        # АВТОМАТИЧЕСКИ ОТКРЫВАЕМ ГЛАВНОЕ МЕНЮ
        # -------------------------------------------------

        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return


# =========================================================
# ШКАЛА 1–10
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
# ОЧИСТКА СОСТОЯНИЯ
# =========================================================

def clear_morning_state(
    context: ContextTypes.DEFAULT_TYPE
):

    for key in [
        "checkin_type",
        "morning_step",
        "energy",
        "sleep",
        "mood",
    ]:

        context.user_data.pop(
            key,
            None
        )