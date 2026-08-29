from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from services.subscription import (
    get_user_plan,
)


# =========================================================
# PRO — ОСНОВНОЙ ЭКРАН
# =========================================================

async def show_pro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Показывает соответствующий экран PRO
    в зависимости от состояния пользователя:

    free
    pro
    pro_expired
    """

    user_id = update.effective_user.id

    plan = get_user_plan(
        user_id
    )

    # =====================================================
    # FREE
    # =====================================================

    if plan == "free":

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ Подключить PRO",
                    callback_data="pro_subscribe"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ Вернуться позже",
                    callback_data="go_menu"
                )
            ],
        ]

        text = (
            "⭐ <b>Дэн PRO</b>\n\n"

            "Ты уже начал выстраивать свою систему.\n"
            "PRO открывает следующий уровень — когда Дэн "
            "может работать с тобой <b>глубже, а не просто шире.</b>\n\n"

            "🧠 <b>Больше памяти</b> — Дэн лучше учитывает "
            "твой путь, решения и то, над чем ты работаешь.\n\n"

            "🎯 <b>Больше пространства для целей</b> — "
            "можно работать не только с одной задачей, "
            "а выстраивать несколько направлений одновременно.\n\n"

            "📈 <b>Глубже анализ прогресса</b> — не только "
            "смотреть на цифры, но и понимать, что реально меняется.\n\n"

            "🔥 <b>Расширенная работа с привычками</b> — "
            "больше инструментов для формирования полезных "
            "и контроля нежелательных привычек.\n\n"

            "💬 <b>Более персональный Дэн</b> — рекомендации "
            "становятся точнее, потому что у него больше "
            "контекста о тебе.\n\n"

            "<b>PRO — когда просто «стараться» уже недостаточно.</b>\n\n"

            "⭐ <b>Стоимость: ХХХ ₽ / месяц</b>"
        )

    # =====================================================
    # PRO ACTIVE
    # =====================================================

    elif plan == "pro":

        from database.subscriptions import (
            get_subscription,
        )

        subscription = get_subscription(
            user_id
        )

        expires_at = "—"

        if subscription:
            expires_at = (
                subscription.get(
                    "expires_at"
                )
                or "—"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "✨ Возможности PRO",
                    callback_data="pro_features"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Вернуться",
                    callback_data="go_menu"
                )
            ],
        ]

        text = (
            "⭐ <b>Дэн PRO</b>\n\n"

            "<b>PRO активен</b> до "
            f"{expires_at}\n\n"

            "Ты открыл расширенную версию Дэна.\n"
            "Теперь можем работать глубже.\n\n"

            "🧠 Расширенная память\n"
            "🎯 Больше возможностей для целей\n"
            "🔥 Расширенная работа с привычками\n"
            "📊 Глубокий анализ прогресса\n"
            "💬 Более персональные рекомендации\n\n"

            "<b>Это твой инструмент. Используй его по максимуму.</b>"
        )

    # =====================================================
    # PRO EXPIRED
    # =====================================================

    elif plan == "pro_expired":

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ Вернуть PRO",
                    callback_data="pro_subscribe"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Продолжить бесплатно",
                    callback_data="go_menu"
                )
            ],
        ]

        text = (
            "⭐ <b>Твой PRO закончился</b>\n\n"

            "Но твой путь никуда не делся.\n\n"

            "Все цели, привычки, история и память Дэна "
            "<b>остались на месте.</b>\n\n"

            "Ты можешь продолжить пользоваться Дэном "
            "бесплатно или вернуть расширенные возможности PRO.\n\n"

            "🧠 Верни глубокую работу с Дэном\n"
            "📊 Верни расширенный анализ\n"
            "🎯 Продолжи работать с большим количеством целей\n"
            "🔥 Верни расширенные возможности привычек\n\n"

            "<b>Ты уже начал. Не обязательно останавливаться здесь.</b>"
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    else:

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Вернуться",
                    callback_data="go_menu"
                )
            ]
        ]

        text = (
            "⭐ <b>Дэн PRO</b>\n\n"
            "Не удалось определить состояние подписки.\n\n"
            "Попробуй открыть раздел ещё раз."
        )

    # =====================================================
    # ОТПРАВКА
    # =====================================================

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

        try:
            await query.edit_message_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

        except Exception as error:

            if "Message is not modified" not in str(error):
                raise

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


# =========================================================
# PRO — ЗАГЛУШКА ВОЗМОЖНОСТЕЙ
# =========================================================

async def show_pro_features(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Экран с возможностями активного PRO.

    Пока это информационная заглушка.
    Позже сюда можно подключить реальные функции.
    """

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Назад к PRO",
                callback_data="pro_back"
            )
        ]
    ]

    text = (
        "✨ <b>Возможности PRO</b>\n\n"

        "🧠 <b>Расширенная память</b>\n"
        "Дэн сможет сохранять больше важного контекста "
        "о твоём пути и использовать его в будущих разговорах.\n\n"

        "🎯 <b>Расширенная работа с целями</b>\n"
        "Можно будет одновременно работать с несколькими "
        "направлениями и связывать их между собой.\n\n"

        "🔥 <b>Расширенная система привычек</b>\n"
        "Больше полезных и нежелательных привычек, "
        "больше возможностей для их контроля.\n\n"

        "📊 <b>Глубокий анализ прогресса</b>\n"
        "Не просто статистика, а понимание динамики, "
        "слабых мест и точек роста.\n\n"

        "💬 <b>Более персональный Дэн</b>\n"
        "Больше контекста — более точные рекомендации "
        "и более глубокий диалог.\n\n"

        "<b>Это только начало.</b>\n"
        "Дэн постепенно будет становиться более "
        "персональным инструментом для твоего развития."
    )

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

        try:
            await query.edit_message_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

        except Exception as error:

            if "Message is not modified" not in str(error):
                raise

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


# =========================================================
# PRO — ПОДКЛЮЧЕНИЕ
# =========================================================

async def subscribe_pro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Пока тестовая заглушка.

    Здесь позже будет реальная оплата.
    """

    keyboard = [
        [
            InlineKeyboardButton(
                "⭐ Подключить PRO",
                callback_data="pro_test_activate"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="pro_back"
            )
        ],
    ]

    text = (
        "⭐ <b>Подключение PRO</b>\n\n"

        "Ты почти у цели.\n\n"

        "После подключения тебе станут доступны "
        "расширенные возможности Дэна для более "
        "глубокой работы над собой.\n\n"

        "💳 <b>Стоимость: ХХХ ₽ / месяц</b>\n\n"

        "Сейчас оплата ещё находится в разработке.\n"
        "Мы пока можем использовать тестовую активацию."
    )

    query = update.callback_query

    if query:

        try:
            await query.answer()
        except Exception:
            pass

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


# =========================================================
# PRO — ТЕСТОВАЯ АКТИВАЦИЯ
# =========================================================


async def test_activate_pro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    from services.subscription import (
        enable_test_pro,
    )

    from handlers.pro_setup import (
        start_pro_setup,
    )

    user_id = update.effective_user.id

    enable_test_pro(
        user_id,
        days=30
    )

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "⭐ PRO активирован!"
            )
        except Exception:
            pass

    # =====================================================
    # СРАЗУ ПОСЛЕ АКТИВАЦИИ — PRO SETUP
    # =====================================================

    await start_pro_setup(
        update,
        context
    )



# =========================================================
# НАЗАД К PRO
# =========================================================

async def back_to_pro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await show_pro(
        update,
        context
    )