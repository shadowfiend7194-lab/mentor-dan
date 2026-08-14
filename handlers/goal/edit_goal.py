from telegram import Update

from telegram.ext import ContextTypes

from handlers.goal.screen import show_goal

from database.goals import (
    get_main_goal,
    create_goal,
    update_goal,
)


# =========================================================
# НАЧАЛО ИЗМЕНЕНИЯ ЦЕЛИ
# =========================================================

async def edit_current_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    context.user_data[
        "goal_edit_state"
    ] = "waiting"

    await query.message.reply_text(
        "✏️ <b>Изменение цели</b>\n\n"
        "Напиши новую формулировку своей главной цели.",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНЕНИЕ НОВОЙ ЦЕЛИ
# =========================================================

async def save_edited_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "goal_edit_state"
    ) != "waiting":

        return False

    new_goal = update.message.text.strip()

    if not new_goal:
        return True

    user_id = update.effective_user.id

    # -----------------------------------------------------
    # Ищем текущую главную цель
    # -----------------------------------------------------

    goal_data = get_main_goal(
        user_id
    )

    # -----------------------------------------------------
    # Обновляем существующую
    # -----------------------------------------------------

    if goal_data:

        update_goal(
            user_id=user_id,
            goal_id=goal_data["id"],
            title=new_goal,
        )

    # -----------------------------------------------------
    # Если цели почему-то нет — создаём
    # -----------------------------------------------------

    else:

        create_goal(
            user_id=user_id,
            title=new_goal,
            is_main=True,
        )

    # -----------------------------------------------------
    # Обновляем временное состояние
    # -----------------------------------------------------

    context.user_data[
        "main_goal"
    ] = new_goal

    context.user_data.pop(
        "goal_edit_state",
        None
    )

    # -----------------------------------------------------
    # Сразу возвращаемся на экран «Моя цель»
    # -----------------------------------------------------

    await show_goal(
        update,
        context
    )

    return True