from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from services.subscription import complete_pro_setup

from database.habits import (
    parse_custom_days,
    format_frequency,
)

from services.dan.pro_setup import (
    can_start_pro_setup,
    get_setup_goals,
    get_current_habit,
    create_setup_state,
    add_setup_goal,
    can_add_setup_goal,
    get_remaining_goal_slots,
    save_setup_difficulty,
    save_setup_motivation,
    save_setup_goal,
    check_setup_goal_conflict,
    prepare_setup_after_goals,
    move_to_next_habit,
    create_setup_habit,
    reset_new_habit_state,
    finish_setup,
)


# =========================================================
# ВСПОМОГАТЕЛЬНОЕ
# =========================================================

def get_state(context):
    return context.user_data.get(
        "pro_setup"
    )


def set_state(
    context,
    state,
):
    context.user_data[
        "pro_setup"
    ] = state


def clear_state(context):
    context.user_data.pop(
        "pro_setup",
        None
    )


# =========================================================
# СТАРТ
# =========================================================

async def start_pro_setup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    if not can_start_pro_setup(
        user_id
    ):
        return

    state = create_setup_state(
        user_id
    )

    set_state(
        context,
        state
    )

    await show_goals_stage(
        update,
        context
    )


# =========================================================
# ЦЕЛИ
# =========================================================

async def show_goals_stage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    goals = get_setup_goals(
        user_id
    )

    lines = [
        "🎯 <b>Давай сначала разберёмся с целями.</b>",
        "",
    ]

    if goals:

        lines.append(
            "Сейчас у тебя есть:"
        )

        lines.append("")

        for goal in goals:

            marker = (
                "⭐"
                if goal.get("is_main")
                else "🎯"
            )

            lines.append(
                f"{marker} {goal.get('title', 'Без названия')}"
            )

    else:

        lines.append(
            "Пока целей нет."
        )

    remaining = get_remaining_goal_slots(
        user_id
    )

    lines.extend(
        [
            "",
            "Есть ли ещё что-то, над чем ты сейчас реально хочешь работать?",
            "",
            "Сначала разберём цели, а потом настроим привычки.",
        ]
    )

    if remaining > 0:

        lines.append(
            f"\nМожно добавить ещё {remaining} "
            f"{'цель' if remaining == 1 else 'цели' if remaining < 5 else 'целей'}."
        )

    keyboard = []

    if remaining > 0:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "➕ Добавить цель",
                    callback_data="pro_setup_add_goal"
                )
            ]
        )

    else:

        lines.extend(
            [
                "",
                "🧠 <b>Целей уже 3 — это максимум.</b>",
                "Давай сначала сфокусируемся на них, "
                "а новые добавим позже, когда будет смысл."
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➡️ Целей достаточно",
                callback_data="pro_setup_goals_done"
            )
        ]
    )
    await send_or_reply(
        update,
        "\n".join(lines),
        keyboard,
    )


# =========================================================
# ДОБАВИТЬ ЦЕЛЬ
# =========================================================

async def pro_setup_add_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    if not can_add_setup_goal(
        user_id
    ):

        await query.message.reply_text(
            "🧠 <b>Стоп.</b>\n\n"
            "У тебя уже 3 цели — это максимум.\n\n"
            "Если набрать ещё, легко начать "
            "распыляться вместо того, чтобы "
            "реально двигаться вперёд.\n\n"
            "Давай сначала доведём эти цели "
            "до результата.",
            parse_mode="HTML"
        )

        return

    state = get_state(
        context
    )

    if not state:
        return

    state["stage"] = "goal_name"

    await query.message.reply_text(
        "🎯 <b>Новая цель</b>\n\n"
        "Напиши её своими словами.\n\n"
        "Например:\n"
        "• Поступить в вуз\n"
        "• Запустить свой проект\n"
        "• Подтянуть английский",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНИТЬ ЦЕЛЬ
# =========================================================

async def save_pro_setup_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get("stage") != "goal_name":
        return False

    title = update.message.text.strip()

    if not title:

        await update.message.reply_text(
            "Напиши название цели текстом."
        )

        return True

    user_id = update.effective_user.id

    goal_id = add_setup_goal(
        user_id,
        title,
    )

    if goal_id is None:

        await update.message.reply_text(
            "🧠 Сейчас новую цель добавить нельзя.\n\n"
            "Проверь, не достиг ли ты лимита "
            "в 3 активных целей."
        )

        return True

    state["stage"] = "goals"

    await update.message.reply_text(
        "✅ <b>Цель добавлена.</b>\n\n"
        f"🎯 {title}",
        parse_mode="HTML"
    )

    await show_goals_stage(
        update,
        context
    )

    return True


# =========================================================
# ЦЕЛИ ЗАКОНЧЕНЫ
# =========================================================

async def pro_setup_goals_done(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    user_id = update.effective_user.id

    has_habits = prepare_setup_after_goals(
        user_id,
        state,
    )

    if not has_habits:

        await show_new_habits_stage(
            update,
            context
        )

        return

    await show_current_habit(
        update,
        context
    )


# =========================================================
# ТЕКУЩАЯ ПРИВЫЧКА
# =========================================================

async def show_current_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    state = get_state(
        context
    )

    if not state:
        return

    habit = get_current_habit(
        user_id,
        state,
    )

    if not habit:

        await show_new_habits_stage(
            update,
            context
        )

        return

    state["stage"] = "difficulty"

    is_good = (
        habit.get("habit_type") == "good"
    )

    icon = (
        "🟢"
        if is_good
        else "🔴"
    )

    if is_good:

        intro = (
            "Для неё определим личную сложность, "
            "поймём, зачем ты хочешь её сформировать, "
            "и свяжем её с подходящей целью."
        )

    else:

        intro = (
            "Для неё определим личную сложность, "
            "разберёмся, почему ты хочешь избавиться "
            "от неё или сократить её, и при необходимости "
            "свяжем её с целью."
        )

    text = (
        f"{icon} <b>Теперь разберём привычку:</b>\n\n"
        f"<b>{habit.get('name', 'Без названия')}</b>\n\n"
        f"{intro}\n\n"
        "Это займёт совсем немного времени."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➡️ Начать",
                callback_data="pro_setup_habit_start"
            )
        ]
    ]

    await send_or_reply(
        update,
        text,
        keyboard,
    )


# =========================================================
# НАЧАТЬ СУЩЕСТВУЮЩУЮ ПРИВЫЧКУ
# =========================================================

async def pro_setup_habit_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    state["stage"] = "difficulty"

    await show_difficulty(
        query.message,
        context
    )


# =========================================================
# СЛОЖНОСТЬ
# =========================================================

async def show_difficulty(
    message,
    context,
):

    keyboard = []

    labels = {
        1: "1️⃣ Очень легко",
        2: "2️⃣ Легко",
        3: "3️⃣ Средне",
        4: "4️⃣ Сложно",
        5: "5️⃣ Очень сложно",
    }

    for difficulty in range(
        1,
        6,
    ):

        keyboard.append(
            [
                InlineKeyboardButton(
                    labels[difficulty],
                    callback_data=(
                        f"pro_setup_difficulty_{difficulty}"
                    )
                )
            ]
        )

    await message.reply_text(
        "🔥 <b>Насколько тебе сложно выполнять "
        "эту привычку регулярно?</b>\n\n"
        "Оцени именно личную сложность для себя.\n\n"
        "1 — почти не требует усилий\n"
        "5 — действительно приходится себя дисциплинировать",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СОХРАНИТЬ СЛОЖНОСТЬ
# =========================================================

async def pro_setup_difficulty(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    try:

        difficulty = int(
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
        return

    user_id = update.effective_user.id

    habit = get_current_habit(
        user_id,
        state,
    )

    if not habit:
        return

    saved = save_setup_difficulty(
        user_id,
        habit["id"],
        difficulty,
    )

    if not saved:

        await query.message.reply_text(
            "Не получилось сохранить сложность. "
            "Попробуй ещё раз."
        )

        return

    state["current_difficulty"] = difficulty
    state["stage"] = "motivation"

    if habit.get("habit_type") == "good":

        text = (
            "🧠 <b>Зачем тебе сформировать эту привычку?</b>\n\n"
            "Напиши своими словами, что ты хочешь "
            "получить благодаря ей.\n\n"
            "Например:\n"
            "«Хочу лучше концентрироваться»\n"
            "«Хочу стать выносливее»\n"
            "«Хочу наконец нормально высыпаться»"
        )

    else:

        text = (
            "🧠 <b>Почему ты хочешь избавиться "
            "от этой привычки или сократить её?</b>\n\n"
            "Напиши своими словами, что тебя в ней "
            "беспокоит и что ты хочешь изменить.\n\n"
            "Например:\n"
            "«Хочу меньше зависать в телефоне»\n"
            "«Хочу перестать откладывать всё на ночь»\n"
            "«Хочу меньше тратить времени впустую»"
        )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# МОТИВАЦИЯ
# =========================================================

async def pro_setup_motivation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get("stage") != "motivation":
        return False

    motivation = update.message.text.strip()

    if not motivation:

        await update.message.reply_text(
            "Напиши хотя бы пару слов о мотивации."
        )

        return True

    user_id = update.effective_user.id

    habit = get_current_habit(
        user_id,
        state,
    )

    if not habit:
        return True

    saved = save_setup_motivation(
        user_id,
        habit["id"],
        motivation,
    )

    if not saved:

        await update.message.reply_text(
            "Не получилось сохранить мотивацию. "
            "Попробуй ещё раз."
        )

        return True

    state["current_motivation"] = motivation
    state["stage"] = "goal"

    await show_habit_goals(
        update,
        context
    )

    return True


# =========================================================
# ВЫБОР ЦЕЛИ ДЛЯ СУЩЕСТВУЮЩЕЙ ПРИВЫЧКИ
# =========================================================

async def show_habit_goals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    state = get_state(
        context
    )

    habit = get_current_habit(
        user_id,
        state,
    )

    goals = get_setup_goals(
        user_id
    )

    keyboard = []

    for goal in goals:

        icon = (
            "⭐"
            if goal.get("is_main")
            else "🎯"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {goal.get('title', 'Без названия')}",
                    callback_data=(
                        f"pro_setup_goal_{goal['id']}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🧠 Для себя / без цели",
                callback_data="pro_setup_goal_none"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ Создать новую цель",
                callback_data="pro_setup_goal_new"
            )
        ]
    )

    if habit and habit.get("goal_id"):

        current_goal = next(
            (
                goal
                for goal in goals
                if goal.get("id")
                == habit.get("goal_id")
            ),
            None,
        )

        if current_goal:

            text = (
                "🎯 <b>Эта привычка уже связана с целью:</b>\n\n"
                f"⭐ {current_goal.get('title', 'Без названия')}\n\n"
                "Выбор уже сохранён. "
                "Если нажать на другую цель, "
                "я не буду менять существующую связь."
            )

        else:

            text = (
                "🎯 <b>Теперь определим связь с целями.</b>\n\n"
                "Эта привычка помогает двигаться "
                "к какой-то конкретной цели?"
            )

    else:

        text = (
            "🎯 <b>Теперь определим связь с целями.</b>\n\n"
            "Эта привычка помогает тебе двигаться "
            "к какой-то конкретной цели?\n\n"
            "Выбери подходящую цель или оставь "
            "привычку для собственного развития."
        )

    await send_or_reply(
        update,
        text,
        keyboard,
    )


# =========================================================
# НОВАЯ ЦЕЛЬ ИЗ ПРИВЯЗКИ
# =========================================================

async def pro_setup_goal_new(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    if not can_add_setup_goal(
        user_id
    ):

        await query.message.reply_text(
            "🧠 <b>Новых целей пока достаточно.</b>\n\n"
            "У тебя уже максимум — 3 цели.\n\n"
            "Не будем распыляться. Сначала "
            "двигаем существующие.",
            parse_mode="HTML"
        )

        return

    state = get_state(
        context
    )

    if not state:
        return

    state["stage"] = "goal_name_from_habit"

    await query.message.reply_text(
        "🎯 <b>Новая цель</b>\n\n"
        "Напиши её название своими словами.\n\n"
        "После создания эта привычка "
        "будет сразу с ней связана.",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНИТЬ НОВУЮ ЦЕЛЬ
# =========================================================

async def save_goal_from_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get(
        "stage"
    ) != "goal_name_from_habit":
        return False

    title = update.message.text.strip()

    if not title:

        await update.message.reply_text(
            "Напиши название цели текстом."
        )

        return True

    user_id = update.effective_user.id

    goal_id = add_setup_goal(
        user_id,
        title,
    )

    if goal_id is None:

        await update.message.reply_text(
            "🧠 Не получилось создать цель.\n\n"
            "Возможно, уже достигнут лимит "
            "в 3 активных целей."
        )

        return True

    habit = get_current_habit(
        user_id,
        state,
    )

    if not habit:

        return True

    saved = save_setup_goal(
        user_id,
        habit["id"],
        goal_id,
    )

    if not saved:

        await update.message.reply_text(
            "Цель создана, но я не смог "
            "связать её с привычкой.\n\n"
            "Не создаём вторую связь автоматически."
        )

        return True

    await update.message.reply_text(
        "✅ <b>Готово.</b>\n\n"
        f"🎯 {title}\n\n"
        "Эта привычка теперь связана "
        "с новой целью.",
        parse_mode="HTML"
    )

    await finish_current_habit(
        update,
        context
    )

    return True


# =========================================================
# ВЫБОР ЦЕЛИ
# =========================================================

async def pro_setup_goal_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    user_id = update.effective_user.id

    habit = get_current_habit(
        user_id,
        state,
    )

    if not habit:
        return

    data = query.data

    # -----------------------------------------------------
    # БЕЗ ЦЕЛИ
    # -----------------------------------------------------

    if data == "pro_setup_goal_none":

        conflict = check_setup_goal_conflict(
            user_id,
            habit["id"],
            None,
        )

        if not conflict["allowed"]:

            current_goal = conflict.get(
                "current_goal"
            )

            goal_title = (
                current_goal.get(
                    "title",
                    "другой цели"
                )
                if current_goal
                else "другой цели"
            )

            await query.message.reply_text(
                "⚠️ <b>Эта привычка уже связана "
                "с целью.</b>\n\n"
                f"🎯 {goal_title}\n\n"
                "Я не буду менять существующую "
                "связь случайным повторным нажатием.",
                parse_mode="HTML"
            )

            return

        saved = save_setup_goal(
            user_id,
            habit["id"],
            None,
        )

        if not saved:

            await query.message.reply_text(
                "Не получилось сохранить выбор."
            )

            return

        await query.message.reply_text(
            "🧠 Готово. Оставляем привычку "
            "для собственного развития."
        )

        await finish_current_habit(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # ID ЦЕЛИ
    # -----------------------------------------------------

    try:

        goal_id = int(
            data.rsplit(
                "_",
                1
            )[1]
        )

    except (
        TypeError,
        ValueError,
        IndexError,
    ):
        return

    # -----------------------------------------------------
    # ПРОВЕРКА КОНФЛИКТА
    # -----------------------------------------------------

    conflict = check_setup_goal_conflict(
        user_id,
        habit["id"],
        goal_id,
    )

    if not conflict["allowed"]:

        current_goal = conflict.get(
            "current_goal"
        )

        goal_title = (
            current_goal.get(
                "title",
                "другой цели"
            )
            if current_goal
            else "другой цели"
        )

        await query.message.reply_text(
            "⚠️ <b>Эта привычка уже привязана "
            "к другой цели.</b>\n\n"
            f"🎯 {goal_title}\n\n"
            "Я не буду менять существующую связь "
            "повторным нажатием.",
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # ПОЛУЧАЕМ ЦЕЛЬ
    # -----------------------------------------------------

    goals = get_setup_goals(
        user_id
    )

    goal = next(
        (
            goal
            for goal in goals
            if goal.get("id") == goal_id
        ),
        None,
    )

    if not goal:
        return

    saved = save_setup_goal(
        user_id,
        habit["id"],
        goal_id,
    )

    if not saved:

        await query.message.reply_text(
            "Не получилось связать привычку "
            "с этой целью."
        )

        return

    await query.message.reply_text(
        "✅ <b>Привычка связана с целью.</b>\n\n"
        f"🎯 {goal.get('title', 'Без названия')}",
        parse_mode="HTML"
    )

    await finish_current_habit(
        update,
        context
    )


# =========================================================
# ЗАВЕРШИТЬ ТЕКУЩУЮ ПРИВЫЧКУ
# =========================================================

async def finish_current_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    state = get_state(
        context
    )

    if not state:
        return

    has_next = move_to_next_habit(
        user_id,
        state,
    )

    if has_next:

        await show_current_habit(
            update,
            context
        )

    else:

        await show_new_habits_stage(
            update,
            context
        )


# =========================================================
# НОВЫЕ ПРИВЫЧКИ
# =========================================================

async def show_new_habits_stage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    state = get_state(
        context
    )

    if not state:
        return

    state["stage"] = "new_habits"

    text = (
        "🔥 <b>Основная настройка готова.</b>\n\n"
        "Теперь Дэн понимает твои цели "
        "и существующие привычки.\n\n"
        "Хочешь добавить новую привычку "
        "сразу с полной PRO-настройкой?"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Добавить привычку",
                callback_data="pro_setup_add_habit"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Пока достаточно",
                callback_data="pro_setup_finish"
            )
        ],
    ]

    await send_or_reply(
        update,
        text,
        keyboard,
    )


# =========================================================
# НОВАЯ ПРИВЫЧКА — ТИП
# =========================================================

async def pro_setup_add_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    reset_new_habit_state(
        state
    )

    state["stage"] = "new_habit_type"

    keyboard = [
        [
            InlineKeyboardButton(
                "🟢 Полезная привычка",
                callback_data="pro_setup_new_good"
            )
        ],
        [
            InlineKeyboardButton(
                "🔴 Нежелательная привычка",
                callback_data="pro_setup_new_bad"
            )
        ],
    ]

    await query.message.reply_text(
        "➕ <b>Новая привычка</b>\n\n"
        "Сначала определим, с чем ты хочешь работать.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# НОВАЯ ПРИВЫЧКА — ТИП
# =========================================================

async def pro_setup_new_habit_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    if query.data == "pro_setup_new_good":

        habit_type = "good"

    elif query.data == "pro_setup_new_bad":

        habit_type = "bad"

    else:
        return

    state["new_habit"][
        "habit_type"
    ] = habit_type

    state["stage"] = "new_habit_name"

    if habit_type == "good":

        text = (
            "🟢 <b>Новая полезная привычка</b>\n\n"
            "Напиши её название.\n\n"
            "Например:\n"
            "• Читать 20 минут\n"
            "• Делать зарядку\n"
            "• Учить английский"
        )

    else:

        text = (
            "🔴 <b>Новая нежелательная привычка</b>\n\n"
            "Напиши, от чего хочешь избавиться "
            "или что хочешь держать под контролем.\n\n"
            "Например:\n"
            "• Слишком много сидеть в телефоне\n"
            "• Ложиться слишком поздно\n"
            "• Есть сладкое вечером"
        )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# НОВАЯ ПРИВЫЧКА — НАЗВАНИЕ
# =========================================================

async def save_new_pro_habit_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get(
        "stage"
    ) != "new_habit_name":
        return False

    name = update.message.text.strip()

    if not name:

        await update.message.reply_text(
            "Напиши название привычки текстом."
        )

        return True

    state["new_habit"][
        "name"
    ] = name

    state["stage"] = "new_habit_frequency"

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 Каждый день",
                callback_data="pro_setup_new_frequency_daily"
            )
        ],
        [
            InlineKeyboardButton(
                "🗓️ Пн–Пт",
                callback_data="pro_setup_new_frequency_weekdays"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ Свои дни",
                callback_data="pro_setup_new_frequency_custom"
            )
        ],
    ]

    await update.message.reply_text(
        "📅 <b>Периодичность</b>\n\n"
        "Как часто хочешь выполнять эту привычку?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

    return True


# =========================================================
# НОВАЯ ПРИВЫЧКА — ПЕРИОДИЧНОСТЬ
# =========================================================

async def pro_setup_new_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    data = query.data

    if data == "pro_setup_new_frequency_daily":

        state["new_habit"][
            "frequency"
        ] = "daily"

        state["new_habit"][
            "schedule_days"
        ] = None

    elif data == "pro_setup_new_frequency_weekdays":

        state["new_habit"][
            "frequency"
        ] = "weekdays"

        state["new_habit"][
            "schedule_days"
        ] = None

    elif data == "pro_setup_new_frequency_custom":

        state["new_habit"][
            "frequency"
        ] = "custom"

        state["stage"] = (
            "new_habit_frequency_custom"
        )

        await query.message.reply_text(
            "✏️ <b>Свои дни</b>\n\n"
            "Напиши дни через запятую.\n\n"
            "Например:\n"
            "<b>Пн, Вт, Чт</b>",
            parse_mode="HTML"
        )

        return

    else:
        return

    state["stage"] = "new_habit_difficulty"

    await show_new_habit_difficulty(
        query.message,
        context
    )


# =========================================================
# СВОИ ДНИ
# =========================================================

async def save_new_pro_habit_days(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get(
        "stage"
    ) != "new_habit_frequency_custom":
        return False

    parsed = parse_custom_days(
        update.message.text.strip()
    )

    if not parsed:

        await update.message.reply_text(
            "⚠️ Не смог распознать дни.\n\n"
            "Например: Пн, Вт, Чт",
        )

        return True

    state["new_habit"][
        "schedule_days"
    ] = ",".join(
        map(
            str,
            parsed
        )
    )

    state["stage"] = (
        "new_habit_difficulty"
    )

    await update.message.reply_text(
        "✅ Периодичность сохранена.",
    )

    await show_new_habit_difficulty(
        update.message,
        context
    )

    return True


# =========================================================
# СЛОЖНОСТЬ НОВОЙ ПРИВЫЧКИ
# =========================================================

async def show_new_habit_difficulty(
    message,
    context,
):

    keyboard = []

    labels = {
        1: "1️⃣ Очень легко",
        2: "2️⃣ Легко",
        3: "3️⃣ Средне",
        4: "4️⃣ Сложно",
        5: "5️⃣ Очень сложно",
    }

    for difficulty in range(
        1,
        6,
    ):

        keyboard.append(
            [
                InlineKeyboardButton(
                    labels[difficulty],
                    callback_data=(
                        f"pro_setup_new_difficulty_{difficulty}"
                    )
                )
            ]
        )

    await message.reply_text(
        "🔥 <b>Насколько тебе сложно выполнять "
        "эту привычку регулярно?</b>\n\n"
        "Оцени именно личную сложность для себя.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СОХРАНИТЬ СЛОЖНОСТЬ НОВОЙ
# =========================================================

async def pro_setup_new_difficulty(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    try:

        difficulty = int(
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
        return

    state["new_habit"][
        "difficulty"
    ] = difficulty

    state["stage"] = (
        "new_habit_motivation"
    )

    habit_type = state[
        "new_habit"
    ].get(
        "habit_type"
    )

    if habit_type == "good":

        text = (
            "🧠 <b>Зачем тебе сформировать "
            "эту привычку?</b>\n\n"
            "Напиши своими словами, что ты хочешь "
            "получить благодаря ей.\n\n"
            "Например:\n"
            "«Хочу больше энергии»\n"
            "«Хочу лучше концентрироваться»"
        )

    else:

        text = (
            "🧠 <b>Почему ты хочешь избавиться "
            "от этой привычки или сократить её?</b>\n\n"
            "Напиши своими словами, что тебя "
            "в ней беспокоит и что ты хочешь изменить.\n\n"
            "Например:\n"
            "«Хочу меньше зависать в телефоне»\n"
            "«Хочу перестать ложиться слишком поздно»"
        )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# МОТИВАЦИЯ НОВОЙ ПРИВЫЧКИ
# =========================================================

async def save_new_pro_habit_motivation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get(
        "stage"
    ) != "new_habit_motivation":
        return False

    motivation = update.message.text.strip()

    if not motivation:

        await update.message.reply_text(
            "Напиши хотя бы пару слов."
        )

        return True

    state["new_habit"][
        "motivation"
    ] = motivation

    state["stage"] = (
        "new_habit_goal"
    )

    await show_new_habit_goals(
        update,
        context
    )

    return True


# =========================================================
# ЦЕЛЬ НОВОЙ ПРИВЫЧКИ
# =========================================================

async def show_new_habit_goals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    state = get_state(
        context
    )

    if not state:
        return

    goals = get_setup_goals(
        user_id
    )

    keyboard = []

    for goal in goals:

        icon = (
            "⭐"
            if goal.get("is_main")
            else "🎯"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {goal.get('title', 'Без названия')}",
                    callback_data=(
                        f"pro_setup_new_goal_{goal['id']}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🧠 Для себя / без цели",
                callback_data="pro_setup_new_goal_none"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ Создать новую цель",
                callback_data="pro_setup_new_goal_create"
            )
        ]
    )

    await send_or_reply(
        update,
        "🎯 <b>К какой цели привяжем привычку?</b>\n\n"
        "Выбери цель, которой эта привычка "
        "помогает двигаться вперёд.\n\n"
        "Если она нужна сама по себе — "
        "выбери «Для себя / без цели».",
        keyboard,
    )


# =========================================================
# СОЗДАТЬ НОВУЮ ЦЕЛЬ ДЛЯ НОВОЙ ПРИВЫЧКИ
# =========================================================

async def pro_setup_new_goal_create(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    if not can_add_setup_goal(
        user_id
    ):

        await query.message.reply_text(
            "🧠 У тебя уже 3 цели — это максимум.\n\n"
            "Выбери одну из существующих целей "
            "для этой привычки.",
            parse_mode="HTML"
        )

        return

    state = get_state(
        context
    )

    if not state:
        return

    state["stage"] = (
        "new_habit_goal_name"
    )

    await query.message.reply_text(
        "🎯 <b>Новая цель</b>\n\n"
        "Напиши её название.\n\n"
        "После создания новая привычка "
        "будет сразу к ней привязана.",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНИТЬ НОВУЮ ЦЕЛЬ
# =========================================================

async def save_new_habit_goal_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return False

    state = get_state(
        context
    )

    if not state:
        return False

    if state.get(
        "stage"
    ) != "new_habit_goal_name":
        return False

    title = update.message.text.strip()

    if not title:

        await update.message.reply_text(
            "Напиши название цели."
        )

        return True

    user_id = update.effective_user.id

    goal_id = add_setup_goal(
        user_id,
        title,
    )

    if goal_id is None:

        await update.message.reply_text(
            "Не получилось создать цель. "
            "У тебя может быть уже 3 активных цели."
        )

        return True

    state["new_habit"][
        "goal_id"
    ] = goal_id

    await update.message.reply_text(
        "✅ <b>Цель создана.</b>\n\n"
        f"🎯 {title}",
        parse_mode="HTML"
    )

    await create_new_pro_habit(
        update,
        context
    )

    return True


# =========================================================
# ВЫБОР ЦЕЛИ НОВОЙ ПРИВЫЧКИ
# =========================================================

async def pro_setup_new_goal_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    if not state:
        return

    user_id = update.effective_user.id

    if query.data == "pro_setup_new_goal_none":

        state["new_habit"][
            "goal_id"
        ] = None

        await create_new_pro_habit(
            update,
            context
        )

        return

    try:

        goal_id = int(
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
        return

    goals = get_setup_goals(
        user_id
    )

    goal = next(
        (
            goal
            for goal in goals
            if goal.get("id") == goal_id
        ),
        None,
    )

    if not goal:
        return

    state["new_habit"][
        "goal_id"
    ] = goal_id

    await create_new_pro_habit(
        update,
        context
    )


# =========================================================
# СОЗДАТЬ НОВУЮ ПРИВЫЧКУ
# =========================================================

async def create_new_pro_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    state = get_state(
        context
    )

    if not state:
        return

    data = state.get(
        "new_habit"
    )

    if not data:
        return

    user_id = update.effective_user.id

    habit_id = create_setup_habit(
        user_id=user_id,
        name=data.get("name"),
        habit_type=data.get("habit_type"),
        frequency=data.get("frequency"),
        schedule_days=data.get(
            "schedule_days"
        ),
        difficulty=data.get(
            "difficulty"
        ),
        motivation=data.get(
            "motivation"
        ),
        goal_id=data.get(
            "goal_id"
        ),
    )

    if not habit_id:

        message = update.effective_message

        if message:

            await message.reply_text(
                "Не получилось создать привычку.\n\n"
                "Попробуй ещё раз."
            )

        return

    habit_type = data.get(
        "habit_type"
    )

    name = data.get(
        "name"
    )

    frequency = data.get(
        "frequency"
    )

    schedule_days = data.get(
        "schedule_days"
    )

    frequency_text = format_frequency(
        frequency,
        schedule_days
    )

    goal_id = data.get(
        "goal_id"
    )

    goal = None

    if goal_id is not None:

        goals = get_setup_goals(
            user_id
        )

        goal = next(
            (
                goal
                for goal in goals
                if goal.get("id") == goal_id
            ),
            None,
        )

    emoji = (
        "🟢"
        if habit_type == "good"
        else "🔴"
    )

    goal_text = (
        f"🎯 {goal.get('title')}"
        if goal
        else "🧠 Без привязки к цели"
    )

    message = update.effective_message

    if message:

        await message.reply_text(
            f"{emoji} <b>Привычка полностью настроена.</b>\n\n"
            f"<b>{name}</b>\n"
            f"📅 {frequency_text}\n"
            f"🎯 {goal_text}\n\n"
            "PRO-настройка сохранена. "
            "Теперь она будет учитываться "
            "в твоём прогрессе.",
            parse_mode="HTML"
        )

    reset_new_habit_state(
        state
    )

    await show_new_habits_stage(
        update,
        context
    )


# =========================================================
# ЗАВЕРШЕНИЕ
# =========================================================

async def pro_setup_finish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    state = get_state(
        context
    )

    finish_setup(
        state
    )

    # Фиксируем завершение PRO Setup в subscriptions.
    # Это критично: повторная активация PRO после окончания
    # должна восстановить данные, а не запускать Setup заново.
    complete_pro_setup(
        update.effective_user.id
    )

    await query.message.reply_text(
        "🔥 <b>Всё готово.</b>\n\n"
        "Теперь Дэн понимает не только то, "
        "что ты делаешь, но и зачем ты это делаешь.\n\n"
        "Дальше система будет смотреть на:\n\n"
        "привычки → стабильность → сложность → "
        "прогресс → цели.\n\n"
        "<b>Работаем.</b>",
        parse_mode="HTML"
    )

    clear_state(
        context
    )


# =========================================================
# СДЕЛАТЬ ПОЗЖЕ
# =========================================================

async def pro_setup_later(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Совместимость со старым callback.

    Кнопка «Сделать позже» больше не показывается в PRO Setup.
    Если старый callback всё же пришёл, Setup не завершается
    и не помечается выполненным — пользователь возвращается
    к текущему этапу настройки.
    """
    query = update.callback_query

    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass

    state = get_state(context)

    if not state:
        await start_pro_setup(update, context)
        return

    stage = state.get("stage")

    if stage == "goals":
        await show_goals_stage(update, context)
    elif stage == "new_habits":
        await show_new_habits_stage(update, context)
    else:
        await show_current_habit(update, context)


# =========================================================
# ТЕКСТОВОЙ РОУТЕР
# =========================================================

async def pro_setup_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    state = get_state(
        context
    )

    if not state:
        return False

    stage = state.get(
        "stage"
    )

    if stage == "goal_name":

        return await save_pro_setup_goal(
            update,
            context
        )

    if stage == "goal_name_from_habit":

        return await save_goal_from_habit(
            update,
            context
        )

    if stage == "motivation":

        return await pro_setup_motivation(
            update,
            context
        )

    if stage == "new_habit_name":

        return await save_new_pro_habit_name(
            update,
            context
        )

    if stage == "new_habit_frequency_custom":

        return await save_new_pro_habit_days(
            update,
            context
        )

    if stage == "new_habit_motivation":

        return await save_new_pro_habit_motivation(
            update,
            context
        )

    if stage == "new_habit_goal_name":

        return await save_new_habit_goal_name(
            update,
            context
        )

    return False


# =========================================================
# УНИВЕРСАЛЬНАЯ ОТПРАВКА
# =========================================================

async def send_or_reply(
    update,
    text,
    keyboard,
):

    markup = InlineKeyboardMarkup(
        keyboard
    )

    query = update.callback_query

    if query:

        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )

        return

    if update.effective_message:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )