import logging
import os

from telegram.error import (
    BadRequest,
    NetworkError,
    TimedOut,
)


# =========================================================
# ЛОГИРОВАНИЕ ОШИБОК
# =========================================================

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("dan_errors")
logger.setLevel(logging.ERROR)
logger.propagate = False

if not logger.handlers:

    file_handler = logging.FileHandler(
        "logs/errors.log",
        encoding="utf-8"
    )

    file_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )


# =========================================================
# ПОНЯТНАЯ ОШИБКА ДЛЯ ПОЛЬЗОВАТЕЛЯ
# =========================================================

def get_friendly_error(error):

    if isinstance(error, TimedOut):

        return (
            "❌ Не удалось подключиться к Telegram.\n"
            "Проверь интернет или VPN и попробуй "
            "запустить Дэна ещё раз."
        )

    if isinstance(error, NetworkError):

        return (
            "❌ Нет стабильного соединения с Telegram.\n"
            "Проверь интернет или VPN."
        )

    if isinstance(error, BadRequest):

        message = str(error)

        if "Message is not modified" in message:

            return (
                "ℹ️ Сообщение уже находится "
                "в нужном состоянии."
            )

        if "Query is too old" in message:

            return (
                "ℹ️ Эта кнопка уже устарела.\n"
                "Открой актуальное меню и попробуй снова."
            )

        return (
            "⚠️ Telegram отклонил запрос.\n"
            "Попробуй ещё раз."
        )

    return (
        "⚠️ Произошла ошибка:\n\n"
        f"<code>{str(error)[:300]}</code>"
    )


# =========================================================
# ГЛОБАЛЬНЫЙ ОБРАБОТЧИК
# =========================================================

async def error_handler(
    update,
    context
):

    error = context.error

    # ПОЛНЫЙ traceback именно в файл
    logger.error(
        "ОШИБКА ДЭНА",
        exc_info=(
            type(error),
            error,
            error.__traceback__
        )
    )

    # =====================================================
    # СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЮ
    # =====================================================

    if update and update.effective_chat:

        try:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_friendly_error(error),
                parse_mode="HTML"
            )

        except Exception as send_error:

            logger.error(
                "Не удалось отправить сообщение об ошибке",
                exc_info=(
                    type(send_error),
                    send_error,
                    send_error.__traceback__
                )
            )