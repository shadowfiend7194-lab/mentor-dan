from telegram import Update

from telegram.ext import ContextTypes

from database.habits import (
    get_user_habits,
    is_completed_today,
    complete_habit,
    is_habit_scheduled_today,
)

from handlers.day.screen import show_day


# =========================================================
# НАЖАТИЕ НА ПРИВЫЧКУ
# =========================================================

async def habit_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        habit_id = int(
            query.data.replace(
                "day_habit_",
                ""
            )
        )

    except ValueError:

        return

    user_id = update.effective_user.id

    habits = get_user_habits(
        user_id
    )

    habit = next(
        (
            item
            for item in habits
            if item["id"] == habit_id
        ),
        None
    )

    if not habit:
        return

    # Не даём отметить привычку
    # в незапланированный день.
    if not is_habit_scheduled_today(
        habit
    ):
        await show_day(
            update,
            context
        )
        return

    completed = is_completed_today(
        habit_id
    )

    complete_habit(
        habit_id=habit_id,
        completed=not completed
    )

    await show_day(
        update,
        context
    )