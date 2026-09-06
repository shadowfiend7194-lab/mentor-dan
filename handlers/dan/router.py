from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_connection
from services.dan.ai import get_dan_response
from database.dan.conversations import save_dan_message
from services.subscription import user_has_pro


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
# FREE / PRO: ЛИМИТ ЗАПРОСОВ ДЭНУ
# =========================================================

FREE_DAN_DAILY_LIMIT = 3
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

DAN_FREE_LIMIT_MESSAGE = (
    "💬 Ты использовал все 3 бесплатных запроса Дэну на сегодня.\n\n"
    "Ничего страшного — возвращайся завтра, и лимит снова будет доступен.\n\n"
    "⭐ А если хочешь общаться с Дэном без этого ограничения, "
    "PRO откроет полный доступ."
)


def _moscow_date():
    return datetime.now(MOSCOW_TZ).date().isoformat()


def _consume_dan_request(user_id):
    """
    Атомарно учитывает один запрос Дэну для FREE-пользователя.

    PRO-пользователи не ограничиваются.

    Лимит считается по календарному дню Москвы.
    Отдельная таблица создаётся автоматически, поэтому
    миграция основной БД не требуется.
    """

    if user_has_pro(user_id):
        return True, None

    usage_date = _moscow_date()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dan_daily_usage (
                user_id INTEGER NOT NULL,
                usage_date TEXT NOT NULL,
                message_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, usage_date)
            )
            """
        )

        cursor.execute(
            """
            SELECT message_count
            FROM dan_daily_usage
            WHERE user_id = ?
              AND usage_date = ?
            """,
            (user_id, usage_date)
        )

        row = cursor.fetchone()
        current_count = row[0] if row else 0

        if current_count >= FREE_DAN_DAILY_LIMIT:
            conn.commit()
            return False, current_count

        new_count = current_count + 1

        cursor.execute(
            """
            INSERT INTO dan_daily_usage (
                user_id,
                usage_date,
                message_count
            )
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, usage_date)
            DO UPDATE SET message_count = excluded.message_count
            """,
            (
                user_id,
                usage_date,
                new_count,
            )
        )

        conn.commit()

        return True, new_count

    finally:
        conn.close()


# =========================================================
# ЗАЩИТА ОТ ПОВТОРНОЙ ОБРАБОТКИ
# =========================================================

def _claim_dan_message(user_id, message_id):
    """
    Атомарно помечает Telegram-сообщение как обрабатываемое.

    Защищает от:
    - повторной обработки одного Telegram-сообщения;
    - двух одновременно работающих экземпляров бота;
    - повторного вызова AI для одного и того же сообщения.
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
    # FREE LIMIT
    # -----------------------------------------------------
    #
    # Важно:
    # - PRO проходит без ограничения;
    # - FREE получает ровно 3 AI-запроса в календарный
    #   день по московскому времени;
    # - 4-й запрос не уходит в AI и не сохраняется
    #   как сообщение диалога;
    # - в 00:00 по Москве лимит автоматически начинается
    #   заново;
    # - история Дэна не удаляется.
    # -----------------------------------------------------

    allowed, usage_count = _consume_dan_request(user_id)

    if not allowed:
        print(
            "🛑 DAN FREE DAILY LIMIT:",
            user_id
        )

        await update.message.reply_text(
            DAN_FREE_LIMIT_MESSAGE
        )

        return True

    print(
        "📊 DAN DAILY USAGE:",
        usage_count if usage_count is not None else "PRO"
    )

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
