from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes


# =========================================================
# ИМЯ
# =========================================================

async def handle_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    name = update.message.text.strip()

    if not name:
        return

    context.user_data["name"] = name
    context.user_data["onboarding_step"] = "age"

    keyboard = [
        [
            InlineKeyboardButton(
                "👦 До 18",
                callback_data="age_under_18"
            ),
            InlineKeyboardButton(
                "🎓 18–25",
                callback_data="age_18_25"
            ),
        ],
        [
            InlineKeyboardButton(
                "💼 26–35",
                callback_data="age_26_35"
            ),
            InlineKeyboardButton(
                "🌟 35+",
                callback_data="age_35_plus"
            ),
        ],
    ]

    await update.message.reply_text(
        f"Приятно познакомиться, {name}! 🤝\n\n"
        "Теперь хочу узнать тебя чуть лучше.\n\n"
        "Сколько тебе лет? 👀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ВОЗРАСТ
# =========================================================

async def handle_age_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    ages = {
        "age_under_18": "До 18",
        "age_18_25": "18–25",
        "age_26_35": "26–35",
        "age_35_plus": "35+",
    }

    age = ages.get(query.data)

    if not age:
        return

    context.user_data["age"] = age
    context.user_data["onboarding_step"] = "main_goal"

    await query.message.reply_text(
        "Отлично! 🙌\n\n"
        "Теперь самое главное — понять, "
        "к чему ты хочешь прийти. 🎯\n\n"
        "Какая у тебя сейчас главная цель?\n\n"
        "Например:\n"
        "🎓 Поступление в университет\n"
        "💪 Улучшить физическую форму\n"
        "💼 Начать своё дело\n"
        "🧠 Навести порядок в жизни\n\n"
        "Напиши её своими словами.",
        parse_mode="HTML"
    )