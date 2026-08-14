from telegram import Update

from telegram.ext import ContextTypes

from database.goals import create_goal

async def handle_main_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    goal = update.message.text.strip()

    if not goal:
        return

    context.user_data["main_goal"] = goal
    create_goal(
        user_id=update.effective_user.id,
        title=goal,
        is_main=True,
    )
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