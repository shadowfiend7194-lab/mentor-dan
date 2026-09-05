from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.connection import get_connection

from database.habits import (
    get_user_habits,
)

from services.subscription import (
    user_has_pro,
)


# =========================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
# =========================================================

def get_habit(
    user_id,
    habit_id
):

    habits = get_user_habits(
        user_id
    )

    return next(
        (
            habit
            for habit in habits
            if habit["id"] == habit_id
        ),
        None
    )


# =========================================================
# ПРОВЕРКА PRO
# =========================================================

async def ensure_pro(
    update
):

    user_id = update.effective_user.id

    if user_has_pro(user_id):
        return True

    query = update.callback_query

    if query:

        try:
            await query.answer(
                "Эта возможность доступна в PRO.",
                show_alert=True
            )
        except Exception:
            pass

    return False


# =========================================================
# СЛОЖНОСТЬ
# =========================================================

async def edit_habit_pro_difficulty(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await ensure_pro(update):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        habit_id = int(
            query.data.replace(
                "habit_difficulty_",
                ""
            )
        )

    except ValueError:

        return

    user_id = update.effective_user.id

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:
        return

    context.user_data[
        "editing_habit_id"
    ] = habit_id

    keyboard = []

    for value in range(1, 6):

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{value}️⃣ {difficulty_label(value)}",
                    callback_data=(
                        f"set_habit_difficulty_{value}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=(
                    f"habit_edit_{habit_id}"
                )
            )
        ]
    )

    current = habit.get(
        "difficulty"
    )

    current_text = (
        f"\n\nСейчас: <b>{difficulty_label(current)}</b> ({current}/5)"
        if current is not None
        else ""
    )

    await query.edit_message_text(
        "🔥 <b>Сложность привычки</b>\n\n"
        "Насколько сложно тебе стабильно "
        "выполнять эту привычку?"
        f"{current_text}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СОХРАНЕНИЕ СЛОЖНОСТИ
# =========================================================

async def set_habit_pro_difficulty(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await ensure_pro(update):
        return

    query = update.callback_query

    if not query:
        return

    try:

        difficulty = int(
            query.data.replace(
                "set_habit_difficulty_",
                ""
            )
        )

    except ValueError:

        return

    if difficulty not in range(1, 6):
        return

    habit_id = context.user_data.get(
        "editing_habit_id"
    )

    if not habit_id:
        return

    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET difficulty = ?
        WHERE id = ?
        AND user_id = ?
        """,
        (
            difficulty,
            habit_id,
            user_id
        )
    )

    conn.commit()
    conn.close()

    try:
        await query.answer(
            "🔥 Сложность сохранена."
        )
    except Exception:
        pass

    from handlers.goal.habits import (
        open_habit,
    )

    await open_habit(
        update,
        context
    )


# =========================================================
# МОТИВАЦИЯ
# =========================================================

async def edit_habit_pro_motivation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await ensure_pro(update):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        habit_id = int(
            query.data.replace(
                "habit_motivation_",
                ""
            )
        )

    except ValueError:

        return

    user_id = update.effective_user.id

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:
        return

    context.user_data[
        "editing_habit_id"
    ] = habit_id

    context.user_data[
        "habit_edit_state"
    ] = "motivation"

    current = habit.get(
        "motivation"
    )

    current_text = ""

    if current:

        current_text = (
            "\n\nТекущая мотивация:\n"
            f"<i>{current}</i>"
        )

    await query.message.reply_text(
        "💬 <b>Мотивация привычки</b>\n\n"
        "Напиши, зачем тебе нужна эта привычка "
        "и почему ты хочешь её придерживаться."
        f"{current_text}",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНЕНИЕ МОТИВАЦИИ
# =========================================================

async def save_habit_pro_motivation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "habit_edit_state"
    ) != "motivation":

        return False

    user_id = update.effective_user.id

    if not user_has_pro(user_id):

        context.user_data.pop(
            "habit_edit_state",
            None
        )

        await update.message.reply_text(
            "🔒 Эта возможность доступна только с PRO."
        )

        return True

    motivation = (
        update.message.text or ""
    ).strip()

    if not motivation:

        await update.message.reply_text(
            "Мотивация не может быть пустой."
        )

        return True

    habit_id = context.user_data.get(
        "editing_habit_id"
    )

    if not habit_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET motivation = ?
        WHERE id = ?
        AND user_id = ?
        """,
        (
            motivation,
            habit_id,
            user_id
        )
    )

    conn.commit()
    conn.close()

    context.user_data.pop(
        "habit_edit_state",
        None
    )

    await update.message.reply_text(
        "✅ <b>Мотивация привычки обновлена.</b>",
        parse_mode="HTML"
    )

    await show_habit_card_after_text(
        update,
        context,
        habit_id
    )

    return True


# =========================================================
# ТЕКСТОВОЙ РОУТЕР PRO-РЕДАКТИРОВАНИЯ
# =========================================================

async def pro_habit_edit_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if context.user_data.get(
        "habit_edit_state"
    ) == "motivation":

        return await save_habit_pro_motivation(
            update,
            context
        )

    return False


# =========================================================
# КАРТОЧКА ПРИВЫЧКИ ПОСЛЕ ТЕКСТОВОГО ВВОДА
# =========================================================

async def show_habit_card_after_text(
    update,
    context,
    habit_id
):

    user_id = update.effective_user.id

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:
        return

    icon = (
        "🟢"
        if habit["habit_type"] == "good"
        else "🔴"
    )

    from database.habits import (
        format_frequency,
    )

    frequency_text = format_frequency(
        habit.get("frequency"),
        habit.get("schedule_days")
    )

    difficulty = habit.get(
        "difficulty"
    )

    goal_id = habit.get(
        "goal_id"
    )

    motivation = habit.get(
        "motivation"
    )

    goal_title = None

    if goal_id:

        try:

            from database.goals import (
                get_user_goals,
            )

            goals = get_user_goals(
                user_id
            )

            goal = next(
                (
                    g
                    for g in goals
                    if g["id"] == goal_id
                ),
                None
            )

            if goal:

                goal_title = (
                    goal.get("title")
                    or goal.get("name")
                )

        except Exception:
            pass

    text = (
        f"{icon} <b>{habit['name']}</b>\n\n"
        f"📅 <b>Периодичность:</b> "
        f"{frequency_text}\n"
    )

    if difficulty is not None:

        text += (
            f"🔥 <b>Сложность:</b> "
            f"{difficulty_label(difficulty)} ({difficulty}/5)\n"
        )

    else:

        text += (
            "🔥 <b>Сложность:</b> "
            "не указана\n"
        )

    if goal_title:

        text += (
            f"🎯 <b>Цель:</b> "
            f"{goal_title}\n"
        )

    else:

        text += (
            "🎯 <b>Цель:</b> "
            "без привязки\n"
        )

    if motivation:

        text += (
            f"💬 <b>Мотивация:</b>\n"
            f"{motivation}\n"
        )

    else:

        text += (
            "💬 <b>Мотивация:</b> "
            "не указана\n"
        )

    text += (
        "\n<b>Что хочешь изменить?</b>"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "✏️ Название",
                callback_data=(
                    f"habit_name_{habit_id}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "📅 Периодичность",
                callback_data=(
                    f"habit_frequency_{habit_id}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "🔥 Сложность",
                callback_data=(
                    f"habit_difficulty_{habit_id}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "🎯 Цель",
                callback_data=(
                    f"habit_goal_{habit_id}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "💬 Мотивация",
                callback_data=(
                    f"habit_motivation_{habit_id}"
                )
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=(
                    "habit_edit_good"
                    if habit["habit_type"] == "good"
                    else "habit_edit_bad"
                )
            )
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ЦЕЛЬ
# =========================================================

async def edit_habit_pro_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await ensure_pro(update):
        return

    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    try:

        habit_id = int(
            query.data.replace(
                "habit_goal_",
                ""
            )
        )

    except ValueError:

        return

    user_id = update.effective_user.id

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:
        return

    context.user_data[
        "editing_habit_id"
    ] = habit_id

    from database.goals import (
        get_user_goals,
    )

    goals = get_user_goals(
        user_id
    )

    keyboard = []

    for goal in goals:

        goal_title = (
            goal.get("title")
            or goal.get("name")
            or "Без названия"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🎯 {goal_title}",
                    callback_data=(
                        f"set_habit_goal_{goal['id']}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🚫 Без привязки",
                callback_data="set_habit_goal_none"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=(
                    f"habit_edit_{habit_id}"
                )
            )
        ]
    )

    if not goals:

        await query.edit_message_text(
            "🎯 <b>Цель привычки</b>\n\n"
            "У тебя пока нет целей, "
            "к которым можно привязать привычку.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Назад",
                            callback_data=(
                                f"habit_edit_{habit_id}"
                            )
                        )
                    ]
                ]
            )
        )

        return

    await query.edit_message_text(
        "🎯 <b>Цель привычки</b>\n\n"
        "Выбери цель, с которой связана "
        "эта привычка:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СОХРАНЕНИЕ ЦЕЛИ
# =========================================================

async def set_habit_pro_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await ensure_pro(update):
        return

    query = update.callback_query

    if not query:
        return

    data = query.data

    if data == "set_habit_goal_none":

        goal_id = None

    else:

        try:

            goal_id = int(
                data.replace(
                    "set_habit_goal_",
                    ""
                )
            )

        except ValueError:

            return

    habit_id = context.user_data.get(
        "editing_habit_id"
    )

    if not habit_id:
        return

    user_id = update.effective_user.id

    # Проверяем, что привычка принадлежит пользователю.
    habit = get_habit(user_id, habit_id)
    if not habit:
        await query.answer("Привычка не найдена.", show_alert=True)
        return

    # Если выбрана цель, она тоже должна принадлежать этому пользователю.
    if goal_id is not None:
        from database.goals import get_user_goals
        valid_goal_ids = {goal["id"] for goal in get_user_goals(user_id) if goal.get("pro_status") != "frozen"}
        if goal_id not in valid_goal_ids:
            await query.answer("Эта цель недоступна.", show_alert=True)
            return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits
        SET goal_id = ?
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            goal_id,
            habit_id,
            user_id
        )
    )

    conn.commit()
    conn.close()

    try:
        await query.answer(
            "🎯 Цель сохранена."
        )
    except Exception:
        pass

    from handlers.goal.habits import (
        open_habit,
    )

    await open_habit(
        update,
        context
    )