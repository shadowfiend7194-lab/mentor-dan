import logging

from telegram.error import (
    BadRequest,
    NetworkError,
    TimedOut,
)


logger = logging.getLogger(__name__)


def get_friendly_error(
    error
):

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


async def error_handler(
    update,
    context
):

    error = context.error

    # Полный traceback сохраняем в лог.
    logger.exception(
        "Ошибка при обработке обновления",
        exc_info=error
    )

    # Если есть пользователь, пытаемся
    # отправить ему понятное сообщение.
    if update and update.effective_chat:

        try:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_friendly_error(error),
                parse_mode="HTML"
            )

        except Exception:

            logger.exception(
                "Не удалось отправить сообщение об ошибке"
            )