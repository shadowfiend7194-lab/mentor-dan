from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardRemove,
)

from telegram.ext import ContextTypes


# =========================================================
# ВРЕМЯ ПОДЪЁМА
# =========================================================

async def ask_wake_up(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Спрашиваем точное время подъёма.
    Пользователь вводит его самостоятельно:
    например, 8:30 или 07:00.
    """

    context.user_data["onboarding_step"] = "wake_up"

    await update.effective_message.reply_text(
        "⏰ Теперь настроим твой режим.\n\n"
        "Во сколько ты обычно просыпаешься?\n\n"
        "Напиши время, например: <b>8:30</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ОБРАБОТКА ВРЕМЕНИ ПОДЪЁМА
# =========================================================

async def handle_wake_up(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Проверяем и сохраняем время подъёма.
    """

    if not update.message:
        return

    text = update.message.text.strip()

    normalized_time = normalize_time(text)

    if normalized_time is None:

        await update.message.reply_text(
            "Не совсем понял время. 🤔\n\n"
            "Напиши его в формате <b>8:30</b> "
            "или <b>07:00</b>.",
            parse_mode="HTML"
        )

        return

    context.user_data[
        "wake_up_time"
    ] = normalized_time

    context.user_data[
        "onboarding_step"
    ] = "sleep_time"

    await ask_sleep_time(
        update,
        context
    )


# =========================================================
# ВРЕМЯ ОТХОДА КО СНУ
# =========================================================

async def ask_sleep_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Спрашиваем точное время отхода ко сну.
    """

    await update.effective_message.reply_text(
        "🌙 А во сколько ты обычно ложишься спать?\n\n"
        "Напиши время, например: <b>23:00</b>",
        parse_mode="HTML"
    )


# =========================================================
# ОБРАБОТКА ВРЕМЕНИ СНА
# =========================================================

async def handle_sleep_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Проверяем и сохраняем время сна.
    """

    if not update.message:
        return

    text = update.message.text.strip()

    normalized_time = normalize_time(text)

    if normalized_time is None:

        await update.message.reply_text(
            "Не совсем понял время. 🤔\n\n"
            "Напиши его в формате <b>23:00</b> "
            "или <b>00:30</b>.",
            parse_mode="HTML"
        )

        return

    context.user_data[
        "sleep_time"
    ] = normalized_time

    context.user_data[
        "onboarding_step"
    ] = "completed"

    await finish_onboarding(
        update,
        context
    )


# =========================================================
# ПРОВЕРКА ВРЕМЕНИ
# =========================================================

def normalize_time(text: str):
    """
    Принимает:
        8:30
        08:30
        23:00
        00:30

    Возвращает:
        HH:MM

    Если формат неправильный — None.
    """

    try:

        value = datetime.strptime(
            text,
            "%H:%M"
        )

        return value.strftime("%H:%M")

    except ValueError:

        return None


# =========================================================
# ЗАВЕРШЕНИЕ ОНБОРДИНГА
# =========================================================

async def finish_onboarding(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Финальный экран онбординга.
    """

    await update.effective_message.reply_text(
        "🔥 Всё готово.\n\n"
        "Теперь я знаю тебя немного лучше.\n\n"
        "Дальше будем работать вместе — "
        "без попыток изменить всю жизнь за один день.\n\n"
        "Маленькие шаги. Каждый день.\n\n"
        "Добро пожаловать. Мы начинаем. 🤝"
    )

    # Убираем временное состояние онбординга,
    # но оставляем собранные данные в user_data.
    context.user_data.pop(
        "onboarding_step",
        None
    )