from telegram import Update
from telegram.ext import ContextTypes

from database.goals import create_goal, get_user_goals


MENU_BUTTONS = {
    "📅 Мой день",
    "🎯 Моя цель",
    "📊 Мой прогресс",
    "💬 Дэн",
    "⚙️ Настройки",
    "⭐ PRO",
}


async def handle_main_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    goal = (update.message.text or "").strip()
    user_id = update.effective_user.id

    # Кнопка главного меню никогда не может стать названием цели.
    # Это защита от старого/зависшего onboarding_step=main_goal.
    if goal in MENU_BUTTONS:
        context.user_data["onboarding_step"] = "completed"
        from handlers.menu import show_menu
        await show_menu(update, context)
        return

    if not goal:
        return

    # На этапе первого онбординга активной цели быть не должно.
    # Если она уже есть (например, пользователь повторно открыл старый state),
    # не создаём вторую скрытую главную цель.
    existing_goals = get_user_goals(user_id)
    if existing_goals:
        context.user_data["onboarding_step"] = "good_habit"
        await update.message.reply_text(
            "🔥 Цель уже сохранена.\n\n"
            "Теперь выберем одну привычку, которая поможет двигаться к ней. 💪\n\n"
            "Выбери один вариант или напиши свой."
        )
        return

    context.user_data["main_goal"] = goal

    goal_id = create_goal(
        user_id=user_id,
        title=goal,
        is_main=True,
    )

    if goal_id is None:
        await update.message.reply_text(
            "❌ Не получилось сохранить цель. Попробуй ещё раз."
        )
        return

    context.user_data["onboarding_step"] = "good_habit"

    await update.message.reply_text(
        "🔥 Хорошая цель.\n\n"
        "Теперь выберем одну привычку, которая поможет двигаться к ней. 💪\n\n"
        "Например:\n"
        "📚 Учиться каждый день\n"
        "🏃 Тренироваться\n"
        "📖 Читать\n"
        "😴 Ложиться спать вовремя\n\n"
        "Выбери один вариант или напиши свой."
    )
