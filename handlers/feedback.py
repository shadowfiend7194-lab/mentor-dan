from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID


async def handle_feedback_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    feedback_type = context.user_data.get(
        "feedback_type"
    )

    if not feedback_type:
        return False

    user = update.effective_user

    if feedback_type == "feature":
        title = "💡 ПРЕДЛОЖЕНИЕ ФУНКЦИИ"
        thank_text = (
            "Спасибо за предложение ❤️\n\n"
            "Я его рассмотрю. Если идея действительно "
            "хорошо впишется в Дэна — обязательно добавим "
            "её в будущих обновлениях."
        )
    else:
        title = "🐛 СООБЩЕНИЕ О ПРОБЛЕМЕ"
        thank_text = (
            "Спасибо, что помог разобраться с проблемой ❤️\n\n"
            "Я посмотрю, что произошло, и постараюсь "
            "исправить это."
        )

    user_info = (
        f"{title}\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
    )

    # -----------------------------------------------------
    # ТЕКСТ
    # -----------------------------------------------------

    if update.message.text:

        message_text = (
            f"{user_info}\n"
            f"📝 Сообщение:\n"
            f"{update.message.text}"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=message_text
        )

    # -----------------------------------------------------
    # ФОТО / СКРИНШОТ
    # -----------------------------------------------------

    elif update.message.photo:

        photo = update.message.photo[-1]

        caption = (
            update.message.caption
            if update.message.caption
            else "Без описания"
        )

        message_text = (
            f"{user_info}\n"
            f"📝 Описание:\n"
            f"{caption}"
        )

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=message_text
        )

    else:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"{user_info}\n"
                "⚠️ Пользователь отправил неподдерживаемый тип сообщения."
            )
        )

    # -----------------------------------------------------
    # ЗАВЕРШАЕМ СОСТОЯНИЕ
    # -----------------------------------------------------

    context.user_data.pop(
        "feedback_type",
        None
    )

    await update.message.reply_text(
        thank_text
    )

    return True