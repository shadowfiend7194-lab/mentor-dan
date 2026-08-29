from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from services.subscription import (
    user_has_pro,
)

from services.dan.pro_habits import (
    get_habit,
    get_available_goals,
    update_habit_pro_data,
    set_habit_goal,
    remove_habit_goal,
)


# =========================================================
# ВСПОМОГАТЕЛЬНОЕ
# =========================================================

def get_habit_id_from_callback(
    update
):

    query = update.callback_query

    if not query:
        return None

    try:

        return int(
            query.data.rsplit(
                "_",
                1
            )[1]
        )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):

        return None


# =========================================================
# КНОПКИ НАЗАД
# =========================================================

def habit_back_markup(
    habit_id
):

    return InlineKeyboardMarkup(
        [

            [

                InlineKeyboardButton(
                    "⬅️ К привычке",
                    callback_data=(
                        f"habit_edit_{habit_id}"
                    )
                )

            ],

            [

                InlineKeyboardButton(
                    "🎯 Моя цель",
                    callback_data="goal_back"
                )

            ],

        ]
    )


# =========================================================
# PRO LOCK
# =========================================================

async def show_pro_locked(
    query,
    feature,
    habit_id
):

    labels = {

        "difficulty":
        "🔥 Сложность",

        "motivation":
        "🧠 Мотивация",

        "goal":
        "🎯 Связанная цель",

    }

    label = labels.get(
        feature,
        "Эта настройка"
    )

    await query.message.reply_text(

        "⭐ <b>Настройка доступна в PRO</b>\n\n"

        f"{label} входит "
        "в расширенные настройки привычки.\n\n"

        "С активной подпиской ты сможешь "
        "менять её в любое время.",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(
            [

                [

                    InlineKeyboardButton(
                        "⭐ Узнать о PRO",
                        callback_data="pro_features"
                    )

                ],

                [

                    InlineKeyboardButton(
                        "⬅️ К привычке",
                        callback_data=(
                            f"habit_edit_{habit_id}"
                        )
                    )

                ],

            ]
        )
    )


# =========================================================
# СЛОЖНОСТЬ
# =========================================================

async def edit_habit_pro_difficulty(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    habit_id = (
        get_habit_id_from_callback(
            update
        )
    )

    if habit_id is None:
        return

    user_id = update.effective_user.id

    if not user_has_pro(
        user_id
    ):

        await show_pro_locked(
            query,
            "difficulty",
            habit_id
        )

        return

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:

        await query.message.reply_text(
            "❌ Привычка не найдена."
        )

        return

    labels = {

        1: "1️⃣ Очень легко",
        2: "2️⃣ Легко",
        3: "3️⃣ Средне",
        4: "4️⃣ Сложно",
        5: "5️⃣ Очень сложно",

    }

    keyboard = []

    for difficulty in range(
        1,
        6
    ):

        current = (

            " ✅"

            if habit.get(
                "difficulty"
            ) == difficulty

            else ""

        )

        keyboard.append(
            [

                InlineKeyboardButton(

                    labels[
                        difficulty
                    ]
                    + current,

                    callback_data=(
                        f"habit_pro_set_difficulty_"
                        f"{habit_id}_"
                        f"{difficulty}"
                    )

                )

            ]
        )

    keyboard.append(
        [

            InlineKeyboardButton(
                "⬅️ К привычке",
                callback_data=(
                    f"habit_edit_{habit_id}"
                )
            )

        ]
    )

    await query.edit_message_text(

        "🔥 <b>Сложность привычки</b>\n\n"

        "Насколько лично тебе сложно "
        "выполнять её регулярно?",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СОХРАНИТЬ СЛОЖНОСТЬ
# =========================================================

async def set_habit_pro_difficulty(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        parts = query.data.split(
            "_"
        )

        habit_id = int(
            parts[-2]
        )

        difficulty = int(
            parts[-1]
        )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):

        return

    user_id = update.effective_user.id

    if not user_has_pro(
        user_id
    ):

        await show_pro_locked(
            query,
            "difficulty",
            habit_id
        )

        return

    if difficulty < 1 or difficulty > 5:
        return

    update_habit_pro_data(

        user_id=user_id,

        habit_id=habit_id,

        difficulty=difficulty,

    )

    await query.message.reply_text(

        f"✅ <b>Сложность обновлена:</b> "
        f"{difficulty}/5",

        parse_mode="HTML",

        reply_markup=habit_back_markup(
            habit_id
        )
    )


# =========================================================
# МОТИВАЦИЯ
# =========================================================

async def edit_habit_pro_motivation(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    habit_id = (
        get_habit_id_from_callback(
            update
        )
    )

    if habit_id is None:
        return

    user_id = update.effective_user.id

    if not user_has_pro(
        user_id
    ):

        await show_pro_locked(
            query,
            "motivation",
            habit_id
        )

        return

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:

        await query.message.reply_text(
            "❌ Привычка не найдена."
        )

        return

    context.user_data[
        "pro_habit_edit_state"
    ] = "motivation"

    context.user_data[
        "pro_habit_edit_id"
    ] = habit_id

    current = habit.get(
        "motivation"
    )

    if current:

        current_text = (
            f"\n\n<b>Сейчас:</b>\n"
            f"{current}"
        )

    else:

        current_text = ""

    if habit.get(
        "habit_type"
    ) == "good":

        explanation = (
            "Напиши, что ты хочешь получить, "
            "сформировав эту привычку."
        )

    else:

        explanation = (
            "Напиши, почему хочешь избавиться "
            "от этой привычки или сократить её."
        )

    await query.message.reply_text(

        "🧠 <b>Мотивация привычки</b>\n\n"

        f"{explanation}\n\n"

        "Напиши своими словами."

        f"{current_text}",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(
            [

                [

                    InlineKeyboardButton(
                        "⬅️ К привычке",
                        callback_data=(
                            f"habit_edit_{habit_id}"
                        )
                    )

                ],

            ]
        )
    )


# =========================================================
# СОХРАНИТЬ МОТИВАЦИЮ
# =========================================================

async def save_habit_pro_motivation(
    update,
    context
):

    if not update.message:
        return False

    if (
        context.user_data.get(
            "pro_habit_edit_state"
        )
        != "motivation"
    ):

        return False

    habit_id = context.user_data.get(
        "pro_habit_edit_id"
    )

    if not habit_id:
        return False

    motivation = (
        update.message.text.strip()
    )

    if not motivation:

        await update.message.reply_text(
            "Напиши хотя бы пару слов "
            "о мотивации."
        )

        return True

    user_id = update.effective_user.id

    if not user_has_pro(
        user_id
    ):

        context.user_data.pop(
            "pro_habit_edit_state",
            None
        )

        context.user_data.pop(
            "pro_habit_edit_id",
            None
        )

        await update.message.reply_text(
            "⭐ PRO больше не активен — "
            "эта настройка сейчас недоступна."
        )

        return True

    update_habit_pro_data(

        user_id=user_id,

        habit_id=habit_id,

        motivation=motivation,

    )

    context.user_data.pop(
        "pro_habit_edit_state",
        None
    )

    context.user_data.pop(
        "pro_habit_edit_id",
        None
    )

    await update.message.reply_text(

        "✅ <b>Мотивация обновлена.</b>",

        parse_mode="HTML",

        reply_markup=habit_back_markup(
            habit_id
        )
    )

    return True


# =========================================================
# СВЯЗАННАЯ ЦЕЛЬ
# =========================================================

async def edit_habit_pro_goal(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    habit_id = (
        get_habit_id_from_callback(
            update
        )
    )

    if habit_id is None:
        return

    user_id = update.effective_user.id

    if not user_has_pro(
        user_id
    ):

        await show_pro_locked(
            query,
            "goal",
            habit_id
        )

        return

    habit = get_habit(
        user_id,
        habit_id
    )

    if not habit:

        await query.message.reply_text(
            "❌ Привычка не найдена."
        )

        return

    goals = get_available_goals(
        user_id
    )

    keyboard = []

    for goal in goals:

        current = (

            " ✅"

            if goal.get(
                "id"
            )
            ==
            habit.get(
                "goal_id"
            )

            else ""

        )

        icon = (

            "⭐"

            if goal.get(
                "is_main"
            )

            else

            "🎯"

        )

        keyboard.append(
            [

                InlineKeyboardButton(

                    f"{icon} "
                    f"{goal.get('title', 'Без названия')}"
                    f"{current}",

                    callback_data=(
                        f"habit_pro_set_goal_"
                        f"{habit_id}_"
                        f"{goal['id']}"
                    )

                )

            ]
        )

    keyboard.append(
        [

            InlineKeyboardButton(

                "🧠 Без цели",

                callback_data=(
                    f"habit_pro_set_goal_"
                    f"{habit_id}_none"
                )

            )

        ]
    )

    keyboard.append(
        [

            InlineKeyboardButton(
                "⬅️ К привычке",
                callback_data=(
                    f"habit_edit_{habit_id}"
                )
            )

        ]
    )

    await query.edit_message_text(

        "🎯 <b>Связанная цель</b>\n\n"

        "Выбери цель, которой помогает "
        "эта привычка.",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СОХРАНИТЬ СВЯЗЬ
# =========================================================

async def set_habit_pro_goal(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    parts = query.data.split(
        "_"
    )

    if len(parts) < 6:
        return

    try:

        habit_id = int(
            parts[4]
        )

    except (
        TypeError,
        ValueError,
    ):

        return

    goal_value = parts[5]

    user_id = update.effective_user.id

    if not user_has_pro(
        user_id
    ):

        await show_pro_locked(
            query,
            "goal",
            habit_id
        )

        return

    if goal_value == "none":

        remove_habit_goal(
            user_id,
            habit_id
        )

        message = (
            "🧠 Привязка к цели убрана."
        )

    else:

        try:

            goal_id = int(
                goal_value
            )

        except ValueError:

            return

        goals = get_available_goals(
            user_id
        )

        valid_ids = {
            goal["id"]
            for goal in goals
        }

        if goal_id not in valid_ids:

            await query.message.reply_text(
                "❌ Такая цель недоступна."
            )

            return

        set_habit_goal(

            user_id=user_id,

            habit_id=habit_id,

            goal_id=goal_id,

        )

        goal = next(
            goal
            for goal in goals
            if goal["id"] == goal_id
        )

        message = (

            "✅ <b>Связанная цель "
            "обновлена.</b>\n\n"

            f"🎯 {goal['title']}"

        )

    await query.message.reply_text(

        message,

        parse_mode="HTML",

        reply_markup=habit_back_markup(
            habit_id
        )
    )


# =========================================================
# ТЕКСТОВОЙ РОУТЕР
# =========================================================

async def pro_habit_edit_text_router(
    update,
    context
):

    if (
        context.user_data.get(
            "pro_habit_edit_state"
        )
        == "motivation"
    ):

        return await save_habit_pro_motivation(
            update,
            context
        )

    return False