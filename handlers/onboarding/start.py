from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


# =========================================================
# НАЧАЛО ОНБОРДИНГА
# =========================================================

async def start_onboarding(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Первый экран онбординга.

    Здесь только приветствие и две кнопки:
    - начать знакомство
    - зачем это нужно
    """

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Начать знакомство",
                callback_data="onboarding_start"
            )
        ],
        [
            InlineKeyboardButton(
                "🔍 Зачем это нужно?",
                callback_data="onboarding_why"
            )
        ],
    ]

    await update.effective_message.reply_text(
        "Привет! 👋\n\n"
        "Я Дэн.\n\n"
        "Твой персональный наставник по дисциплине.\n\n"
        "Я помогу тебе выстроить систему, "
        "которая позволит двигаться к своим целям "
        "без постоянного давления на себя.\n\n"
        "Готов начать? 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# «ЗАЧЕМ ЭТО НУЖНО?»
# =========================================================

async def onboarding_why(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Экран объяснения.
    После него пользователь получает только одну кнопку —
    «Начать знакомство».
    """

    query = update.callback_query

    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Начать знакомство",
                callback_data="onboarding_start"
            )
        ]
    ]

    await query.edit_message_text(
        "Дисциплина — это не про то, чтобы заставлять "
        "себя делать всё идеально.\n\n"
        "Это про маленькие действия, которые ты "
        "повторяешь каждый день.\n\n"
        "Я помогу тебе определить цели, "
        "сформировать полезные привычки, "
        "избавиться от тех, которые мешают, "
        "и постепенно выстроить свой ритм.\n\n"
        "Без гонки. Без перегруза. "
        "Но с результатом. 💪",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ПЕРЕХОД К ЗНАКОМСТВУ
# =========================================================

async def onboarding_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Переход к следующему этапу.
    Сам профиль пока не реализуем здесь.
    """

    query = update.callback_query

    await query.answer()

    # Временное состояние онбординга.
    context.user_data["onboarding"] = True
    context.user_data["onboarding_step"] = "name"

    await query.edit_message_text(
        "Хорошо. Давай познакомимся поближе. 👋\n\n"
        "Как мне тебя называть?"
    )