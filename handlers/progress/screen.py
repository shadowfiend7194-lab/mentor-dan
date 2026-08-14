from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.progress import get_progress_summary


# =========================================================
# АНАЛИЗ ПОКАЗАТЕЛЯ
# =========================================================

def analyze_energy(value):

    if value >= 8:
        return (
            "Отличный уровень ресурса. "
            "Продолжай держать такой ритм."
        )

    if value >= 6:
        return (
            "Хороший показатель. "
            "Ресурс в целом стабильный."
        )

    if value >= 4:
        return (
            "Ресурс нестабилен. "
            "Стоит обратить внимание на восстановление."
        )

    return (
        "Ресурс низкий. "
        "Сейчас особенно важно не перегружать себя."
    )
    
    if value == 0:
        return "Пока недостаточно данных. Заполняй чек-ины, и Дэн начнёт видеть твой прогресс."
    
    
    if energy:
         f"{analyze_energy(energy)}"

    else:
        "Пока нет данных по энергии."
        

def analyze_sleep(value):

    if value >= 8:
        return (
            "Очень хороший показатель. "
            "Продолжай сохранять стабильный режим."
        )

    if value >= 6:
        return (
            "Неплохой результат, но есть куда улучшаться. "
            "Стабильность режима будет полезна."
        )

    if value >= 4:
        return (
            "Сон сейчас одна из зон роста. "
            "Стоит уделить ему больше внимания."
        )

    return (
        "Качество сна низкое. "
        "Это важная зона для восстановления."
    )


def analyze_mood(value):

    if value >= 8:
        return (
            "Отличный эмоциональный фон. "
            "Сохраняй то, что помогает его поддерживать."
        )

    if value >= 6:
        return (
            "Настрой в целом хороший и стабильный."
        )

    if value >= 4:
        return (
            "Эмоциональный фон нестабилен. "
            "Стоит наблюдать за причинами."
        )

    return (
        "Настрой сейчас проседает. "
        "Важно обратить внимание на своё состояние."
    )


def analyze_stress(value):

    if value <= 3:
        return (
            "Стресс под контролем."
        )

    if value <= 5:
        return (
            "Умеренный уровень. "
            "Пока ситуация выглядит стабильной."
        )

    if value <= 7:
        return (
            "Это одна из зон роста. "
            "Стоит внимательнее следить за нагрузкой."
        )

    return (
        "Высокий стресс. "
        "Этой зоне сейчас стоит уделить особое внимание."
    )


def analyze_evening(value):

    if value >= 8:
        return (
            "В целом дни проходят очень хорошо."
        )

    if value >= 6:
        return (
            "В целом дни проходят нормально. "
            "Есть потенциал для стабильного роста."
        )

    if value >= 4:
        return (
            "Дни проходят нестабильно. "
            "Есть смысл посмотреть на повторяющиеся причины."
        )

    return (
        "Средняя оценка дня низкая. "
        "Стоит внимательнее разобрать, что мешает."
    )


# =========================================================
# ЭКРАН «МОЙ ПРОГРЕСС»
# =========================================================

async def show_progress(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    stats = get_progress_summary(
        user_id
    )

    # =====================================================
    # ОСНОВНЫЕ ПОКАЗАТЕЛИ
    # =====================================================

    best_streak = stats[
        "best_streak"
    ]

    week_completed = stats[
        "week_completed"
    ]

    week_total = stats[
        "week_total"
    ]

    energy = stats[
        "energy"
    ]

    sleep = stats[
        "sleep"
    ]

    mood = stats[
        "mood"
    ]

    stress = stats[
        "stress"
    ]

    evening_score = stats[
        "evening_score"
    ]

    # =====================================================
    # ТЕКСТ
    # =====================================================

    text = (
        "📊 <b>Мой прогресс</b>\n\n"

        f"🔥 <b>Лучшая серия:</b> "
        f"{best_streak} дн.\n"

        f"✅ <b>Выполнено за неделю:</b> "
        f"{week_completed} / {week_total}\n\n"

        "🧠 <b>Состояние</b>\n\n"

        f"⚡ <b>Средняя энергия:</b> "
        f"{energy} / 10\n"
        f"{analyze_energy(energy)}\n\n"

        f"😴 <b>Среднее качество сна:</b> "
        f"{sleep} / 10\n"
        f"{analyze_sleep(sleep)}\n\n"

        f"🙂 <b>Средний настрой:</b> "
        f"{mood} / 10\n"
        f"{analyze_mood(mood)}\n\n"

        f"😰 <b>Средний стресс:</b> "
        f"{stress} / 10\n"
        f"{analyze_stress(stress)}\n\n"

        "🌙 <b>Средняя оценка дня:</b> "
        f"{evening_score} / 10\n"
        f"{analyze_evening(evening_score)}"
    )

    # =====================================================
    # КНОПКИ
    # =====================================================

    keyboard = [
        [
            InlineKeyboardButton(
                "🏆 Достижения",
                callback_data="progress_achievements"
            )
        ],
        [
            InlineKeyboardButton(
                "🛤️ История пути",
                callback_data="progress_history"
            )
        ],
        [
            InlineKeyboardButton(
                "🧠 Недельный анализ",
                callback_data="progress_weekly"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="go_menu"
            )
        ],
    ]

    
    
    markup = InlineKeyboardMarkup(
    keyboard
    )


    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )