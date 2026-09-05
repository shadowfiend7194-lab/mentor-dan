from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_connection
from services.dan.ai import get_dan_response
from database.dan.conversations import save_dan_message


# =========================================================
# КНОПКИ НИЖНЕГО МЕНЮ
# =========================================================

MENU_BUTTONS = {
    "💬 Дэн",
    "📅 Мой день",
    "📊 Мой прогресс",
    "🎯 Моя цель",
    "⭐ Pro",
    "⭐ PRO",
    "⚙️ Настройки",
}


# =========================================================
# ЗАЩИТА ОТ ПОВТОРНОЙ ОБРАБОТКИ
# =========================================================

def _claim_dan_message(user_id, message_id):
    """
    Атомарно помечает Telegram-сообщение как обрабатываемое.

    Зачем это нужно:
    - защищает от двойного запуска одного и того же handler;
    - защищает от двух одновременно запущенных экземпляров бота;
    - не блокирует два разных сообщения пользователя;
    - не требует изменения существующей структуры dan_messages.

    Если сообщение уже было обработано, возвращает False.
    """

    if message_id is None:
        return True

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dan_processed_messages (
                user_id INTEGER NOT NULL,
                telegram_message_id INTEGER NOT NULL,
                processed_at TEXT NOT NULL,
                PRIMARY KEY (user_id, telegram_message_id)
            )
            """
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO dan_processed_messages (
                user_id,
                telegram_message_id,
                processed_at
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                message_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

        claimed = cursor.rowcount == 1
        conn.commit()
        return claimed

    finally:
        conn.close()


# =========================================================
# ОТКРЫТИЕ ВКЛАДКИ ДЭН
# =========================================================

async def open_dan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.callback_query:
        return

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    context.user_data["dan_active"] = True

    await query.message.reply_text(
        "🧠 <b>Дэн</b>\n\n"
        "Я твой персональный наставник.\n\n"
        "Здесь ты можешь свободно писать мне "
        "о своих целях, дисциплине, привычках, "
        "состоянии или проблемах.\n\n"
        "Я буду учитывать то, что уже знаю о тебе, "
        "и помогать тебе двигаться вперёд "
        "без лишнего давления.\n\n"
        "Пиши.",
        parse_mode="HTML"
    )


# =========================================================
# ОБРАБОТКА СООБЩЕНИЙ ДЭНУ
# =========================================================

async def dan_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print("🔥 DAN_TEXT_ROUTER ENTERED")

    if not update.message:
        print("❌ DAN: NO MESSAGE")
        return False

    user_message = (update.message.text or "").strip()

    if not user_message:
        print("❌ DAN: EMPTY MESSAGE")
        return True

    # -----------------------------------------------------
    # ЕСЛИ НАЖАТА КНОПКА НИЖНЕГО МЕНЮ
    # -----------------------------------------------------

    if user_message in MENU_BUTTONS:
        print("🚪 DAN CLOSED BY MENU BUTTON:", user_message)
        close_dan(context)
        return False

    # -----------------------------------------------------
    # ДЭН НЕ АКТИВЕН
    # -----------------------------------------------------

    if not context.user_data.get("dan_active"):
        print("❌ DAN NOT ACTIVE")
        return False

    user_id = update.effective_user.id
    telegram_message_id = update.message.message_id

    print("👤 DAN USER ID:", user_id)
    print("💬 DAN MESSAGE:", user_message)
    print("🆔 TELEGRAM MESSAGE ID:", telegram_message_id)

    # -----------------------------------------------------
    # АТОМАРНАЯ ЗАЩИТА ОТ ДУБЛЯ
    # -----------------------------------------------------
    #
    # Это ключевой фикс текущей проблемы.
    # Если одно и то же Telegram-сообщение каким-либо образом
    # попало в router второй раз, второй вызов НЕ пойдёт в AI.
    #
    # Благодаря SQLite-защите это работает даже если случайно
    # запущены два экземпляра бота одновременно.

    if not _claim_dan_message(
        user_id,
        telegram_message_id
    ):
        print(
            "🛑 DAN DUPLICATE MESSAGE IGNORED:",
            telegram_message_id
        )
        return True

    # -----------------------------------------------------
    # СОХРАНЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    # -----------------------------------------------------

    save_dan_message(
        user_id=user_id,
        role="user",
        message=user_message
    )

    # -----------------------------------------------------
    # ПОЛУЧАЕМ ОТВЕТ ДЭНА
    # -----------------------------------------------------

    print("🧠 CALLING get_dan_response...")

    try:
        response = get_dan_response(
            user_id=user_id,
            user_message=user_message
        )

        print("✅ DAN RESPONSE CREATED")
        print("🤖 RESPONSE:", response)

    except Exception as error:
        print("❌ DAN ERROR:", repr(error))

        await update.message.reply_text(
            "⚠️ Дэн временно не смог сформировать ответ.\n\n"
            "Мы уже разбираемся."
        )

        return True

    # -----------------------------------------------------
    # ПУСТОЙ ОТВЕТ
    # -----------------------------------------------------

    if not response:
        print("❌ EMPTY DAN RESPONSE")

        await update.message.reply_text(
            "🤔 Дэн пока не смог сформировать ответ."
        )

        return True

    # -----------------------------------------------------
    # ОТПРАВЛЯЕМ ОТВЕТ
    # -----------------------------------------------------

    print("📤 SENDING DAN RESPONSE...")

    await update.message.reply_text(
        response
    )

    save_dan_message(
        user_id=user_id,
        role="assistant",
        message=response
    )

    print("✅ DAN RESPONSE SENT")

    return True


# =========================================================
# ВЫХОД ИЗ ДЭНА
# =========================================================

def close_dan(
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.pop(
        "dan_active",
        None
    )

    print("🚪 DAN ACTIVE STATE CLOSED")
