from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import (
    get_user_habits,
    create_habit,
    parse_custom_days,
    format_frequency,
    FREE_MAX_GOOD_HABITS,
    FREE_MAX_BAD_HABITS,
    PRO_MAX_GOOD_HABITS,
    PRO_MAX_BAD_HABITS,
)

from services.subscription import (
    user_has_pro,
)

from services.dan.pro_habits import (
    get_available_goals,
    set_habit_goal,
)


# =========================================================
# ДОБАВЛЕНИЕ НОВОЙ ПРИВЫЧКИ
# =========================================================

async def open_add_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    keyboard = [
        [
            InlineKeyboardButton(
                "🟢 Полезная привычка",
                callback_data="add_habit_good"
            )
        ],
        [
            InlineKeyboardButton(
                "🔴 Нежелательная привычка",
                callback_data="add_habit_bad"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="goal_habits"
            )
        ],
    ]

    await query.edit_message_text(
        "⭐ <b>Новая привычка</b>\n\n"
        "Что хочешь добавить?\n\n"
        "🟢 <b>Полезная</b> — то, что хочешь "
        "делать чаще.\n"
        "🔴 <b>Нежелательная</b> — то, от чего хочешь "
        "постепенно избавиться.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ПРОВЕРКА ЛИМИТА
# =========================================================

def get_habit_counts(user_id):

    habits = get_user_habits(
        user_id
    )

    good_count = sum(
        1
        for habit in habits
        if habit["habit_type"] == "good"
    )

    bad_count = sum(
        1
        for habit in habits
        if habit["habit_type"] == "bad"
    )

    return good_count, bad_count


# =========================================================
# ЛИМИТ
# =========================================================

async def show_habit_limit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query:

        await query.answer()

        await query.edit_message_text(
            "⚠️ <b>Не распыляйся.</b>\n\n"
            "У тебя уже максимальное количество "
            "привычек этого типа.\n\n"
            "⭐ PRO позволяет иметь:\n\n"
            f"🟢 до <b>{PRO_MAX_GOOD_HABITS}</b> полезных привычек\n"
            f"🔴 до <b>{PRO_MAX_BAD_HABITS}</b> нежелательных привычек\n\n"
            "<b>Стабильность важнее количества.</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Назад",
                            callback_data="goal_habits"
                        )
                    ]
                ]
            )
        )


# =========================================================
# ПОЛЕЗНАЯ ПРИВЫЧКА
# =========================================================

async def add_good_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    user_id = update.effective_user.id

    good_count, _ = get_habit_counts(
        user_id
    )

    max_good = (
        PRO_MAX_GOOD_HABITS
        if user_has_pro(user_id)
        else FREE_MAX_GOOD_HABITS
    )

    if good_count >= max_good:

        await show_habit_limit(
            update,
            context
        )

        return

    await query.answer()

    context.user_data[
        "add_habit_type"
    ] = "good"

    context.user_data[
        "add_habit_state"
    ] = "name"

    await query.edit_message_text(
        "🟢 <b>Новая полезная привычка</b>\n\n"
        "Напиши её название.\n\n"
        "Например:\n"
        "• Читать 20 минут\n"
        "• Делать зарядку\n"
        "• Учить английский",
        parse_mode="HTML"
    )


# =========================================================
# НЕЖЕЛАТЕЛЬНАЯ ПРИВЫЧКА
# =========================================================

async def add_bad_habit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    user_id = update.effective_user.id

    _, bad_count = get_habit_counts(
        user_id
    )

    max_bad = (
        PRO_MAX_BAD_HABITS
        if user_has_pro(user_id)
        else FREE_MAX_BAD_HABITS
    )

    if bad_count >= max_bad:

        await show_habit_limit(
            update,
            context
        )

        return

    await query.answer()

    context.user_data[
        "add_habit_type"
    ] = "bad"

    context.user_data[
        "add_habit_state"
    ] = "name"

    await query.edit_message_text(
        "🔴 <b>Новая нежелательная привычка</b>\n\n"
        "Напиши, от чего хочешь избавиться "
        "или что хочешь держать под контролем.\n\n"
        "Например:\n"
        "• Слишком много сидеть в телефоне\n"
        "• Ложиться слишком поздно\n"
        "• Есть сладкое вечером",
        parse_mode="HTML"
    )


# =========================================================
# НАЗВАНИЕ → ПЕРИОДИЧНОСТЬ
# =========================================================

async def save_new_habit_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "add_habit_state"
    ) != "name":

        return False

    name = update.message.text.strip()

    if not name:

        await update.message.reply_text(
            "Напиши название привычки текстом."
        )

        return True

    context.user_data[
        "add_habit_name"
    ] = name

    context.user_data[
        "add_habit_state"
    ] = "frequency"

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 Каждый день",
                callback_data="add_habit_frequency_daily"
            )
        ],
        [
            InlineKeyboardButton(
                "🗓️ Пн–Пт",
                callback_data="add_habit_frequency_weekdays"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ Свои дни",
                callback_data="add_habit_frequency_custom"
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
# ВЫБОР ПЕРИОДИЧНОСТИ
# =========================================================

async def add_habit_frequency_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    data = query.data

    await query.answer()

    if data == "add_habit_frequency_daily":

        context.user_data[
            "add_habit_frequency"
        ] = "daily"

        context.user_data[
            "add_habit_schedule_days"
        ] = None

    elif data == "add_habit_frequency_weekdays":

        context.user_data[
            "add_habit_frequency"
        ] = "weekdays"

        context.user_data[
            "add_habit_schedule_days"
        ] = None

    elif data == "add_habit_frequency_custom":

        context.user_data[
            "add_habit_frequency"
        ] = "custom"

        context.user_data[
            "add_habit_state"
        ] = "frequency_custom"

        await query.message.reply_text(
            "✏️ <b>Свои дни</b>\n\n"
            "Напиши дни через запятую.\n\n"
            "Например:\n"
            "<b>Пн, Вт, Чт</b>\n\n"
            "Можно использовать и полные названия:\n"
            "<b>понедельник, среда, пятница</b>",
            parse_mode="HTML"
        )

        return

    if user_has_pro(update.effective_user.id):

        context.user_data[
            "add_habit_state"
        ] = "difficulty"

        await show_habit_difficulty(
            query.message,
            context
        )

    else:

        await create_habit_after_goal(
            update,
            context,
            None,
        )


# =========================================================
# СВОИ ДНИ
# =========================================================

async def save_custom_habit_days(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "add_habit_state"
    ) != "frequency_custom":

        return False

    text = update.message.text.strip()

    parsed = parse_custom_days(
        text
    )

    if not parsed:

        await update.message.reply_text(
            "⚠️ Не смог распознать дни.\n\n"
            "Напиши их через запятую.\n"
            "Например: <b>Пн, Вт, Чт</b>",
            parse_mode="HTML"
        )

        return True

    schedule_days = ",".join(
        map(
            str,
            parsed
        )
    )

    context.user_data[
        "add_habit_schedule_days"
    ] = schedule_days

    if user_has_pro(update.effective_user.id):

        context.user_data[
            "add_habit_state"
        ] = "difficulty"

        await update.message.reply_text(
            "✅ Периодичность сохранена.\n\n"
            "Теперь давай оценим сложность привычки.",
            parse_mode="HTML"
        )

        await show_habit_difficulty(
            update.message,
            context
        )

    else:

        await create_habit_after_goal(
            update,
            context,
            None,
        )

    return True


# =========================================================
# СЛОЖНОСТЬ
# =========================================================

async def show_habit_difficulty(
    message,
    context
):

    keyboard = [
        [
            InlineKeyboardButton(
                "1️⃣ Очень легко",
                callback_data="add_habit_difficulty_1"
            )
        ],
        [
            InlineKeyboardButton(
                "2️⃣ Легко",
                callback_data="add_habit_difficulty_2"
            )
        ],
        [
            InlineKeyboardButton(
                "3️⃣ Средне",
                callback_data="add_habit_difficulty_3"
            )
        ],
        [
            InlineKeyboardButton(
                "4️⃣ Сложно",
                callback_data="add_habit_difficulty_4"
            )
        ],
        [
            InlineKeyboardButton(
                "5️⃣ Очень сложно",
                callback_data="add_habit_difficulty_5"
            )
        ],
    ]

    await message.reply_text(
        "🎯 <b>Насколько сложной кажется эта привычка?</b>\n\n"
        "Оцени её по шкале от 1 до 5.\n\n"
        "1 — почти не требует усилий\n"
        "5 — действительно придётся себя дисциплинировать",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ВЫБОР СЛОЖНОСТИ
# =========================================================

async def add_habit_difficulty_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        difficulty = int(
            query.data.split(
                "_"
            )[-1]
        )

    except (
        TypeError,
        ValueError,
    ):

        return

    context.user_data[
        "add_habit_difficulty"
    ] = difficulty

    context.user_data[
        "add_habit_state"
    ] = "motivation"

    habit_type = context.user_data.get(
        "add_habit_type"
    )

    if habit_type == "good":

        text = (
            "🧠 <b>Зачем тебе эта привычка?</b>\n\n"
            "Напиши, что ты хочешь получить, "
            "сформировав эту привычку.\n\n"
            "Например:\n"
            "«Хочу больше энергии»\n"
            "«Хочу лучше концентрироваться»\n"
            "«Хочу стать выносливее»"
        )

    else:

        text = (
            "🧠 <b>Почему ты хочешь изменить эту привычку?</b>\n\n"
            "Напиши, почему хочешь избавиться "
            "от неё или сократить её.\n\n"
            "Например:\n"
            "«Хочу меньше зависать в телефоне»\n"
            "«Хочу наладить режим»\n"
            "«Хочу перестать откладывать сон»"
        )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# МОТИВАЦИЯ → ВЫБОР ЦЕЛИ
# =========================================================

async def save_habit_motivation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if context.user_data.get(
        "add_habit_state"
    ) != "motivation":

        return False

    motivation = update.message.text.strip()

    if not motivation:

        await update.message.reply_text(
            "Напиши пару слов о том, "
            "зачем тебе эта привычка."
        )

        return True

    context.user_data[
        "add_habit_motivation"
    ] = motivation

    user_id = update.effective_user.id

    # -----------------------------------------------------
    # ПОЛУЧАЕМ ЦЕЛИ
    # -----------------------------------------------------

    goals = get_available_goals(
        user_id
    )

    # -----------------------------------------------------
    # ЕСЛИ ЦЕЛЕЙ НЕТ
    # -----------------------------------------------------

    if not goals:

        await create_habit_after_goal(
            update,
            context,
            None
        )

        return True

    # -----------------------------------------------------
    # ЕСЛИ ЦЕЛИ ЕСТЬ — СПРАШИВАЕМ
    # -----------------------------------------------------

    context.user_data[
        "add_habit_state"
    ] = "goal"

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
                    f"{icon} "
                    f"{goal.get('title', 'Без названия')}",
                    callback_data=(
                        f"add_habit_goal_{goal['id']}"
                    )
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🧠 Для себя / без цели",
                callback_data="add_habit_goal_none"
            )
        ]
    )

    await update.message.reply_text(
        "🎯 <b>К какой цели привязать привычку?</b>\n\n"
        "Выбери направление, которому эта привычка "
        "помогает двигаться вперёд.\n\n"
        "Если привычка не относится к конкретной "
        "цели — выбери «Для себя / без цели».",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

    return True


# =========================================================
# ВЫБОР ЦЕЛИ
# =========================================================

async def add_habit_goal_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if context.user_data.get(
        "add_habit_state"
    ) != "goal":

        return

    user_id = update.effective_user.id

    data = query.data

    if data == "add_habit_goal_none":

        goal_id = None

    else:

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

        goals = get_available_goals(
            user_id
        )

        valid_goal_ids = {
            goal.get("id")
            for goal in goals
        }

        if goal_id not in valid_goal_ids:

            await query.message.reply_text(
                "❌ Эта цель больше недоступна."
            )

            return

    await create_habit_after_goal(
        update,
        context,
        goal_id
    )


# =========================================================
# СОЗДАНИЕ ПРИВЫЧКИ ПОСЛЕ ВЫБОРА ЦЕЛИ
# =========================================================

async def create_habit_after_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    goal_id=None,
):

    user_id = update.effective_user.id

    pro_active = user_has_pro(user_id)

    if not pro_active:
        goal_id = None

    habit_id = create_habit(
        user_id=user_id,
        name=context.user_data.get(
            "add_habit_name"
        ),
        habit_type=context.user_data.get(
            "add_habit_type"
        ),
        frequency=context.user_data.get(
            "add_habit_frequency",
            "daily"
        ),
        schedule_days=context.user_data.get(
            "add_habit_schedule_days"
        ),
        difficulty=(
            context.user_data.get("add_habit_difficulty")
            if pro_active
            else None
        ),
        motivation=(
            context.user_data.get("add_habit_motivation")
            if pro_active
            else None
        )
    )

    # -----------------------------------------------------
    # СОХРАНЯЕМ СВЯЗЬ С ЦЕЛЬЮ
    # -----------------------------------------------------

    if (
        habit_id is not None
        and goal_id is not None
    ):

        set_habit_goal(
            user_id=user_id,
            habit_id=habit_id,
            goal_id=goal_id,
        )

    # -----------------------------------------------------
    # ДАННЫЕ ДЛЯ ФИНАЛЬНОГО СООБЩЕНИЯ
    # -----------------------------------------------------

    habit_type = context.user_data.get(
        "add_habit_type"
    )

    name = context.user_data.get(
        "add_habit_name"
    )

    frequency = context.user_data.get(
        "add_habit_frequency",
        "daily"
    )

    schedule_days = context.user_data.get(
        "add_habit_schedule_days"
    )

    difficulty = context.user_data.get(
        "add_habit_difficulty"
    )

    difficulty_text = (
        f"{difficulty}/5"
        if difficulty is not None
        else "—"
    )

    frequency_text = format_frequency(
        frequency,
        schedule_days
    )

    selected_goal = None

    if goal_id is not None:

        goals = get_available_goals(
            user_id
        )

        selected_goal = next(
            (
                goal
                for goal in goals
                if goal.get("id") == goal_id
            ),
            None
        )

    # -----------------------------------------------------
    # ОЧИСТКА СОСТОЯНИЯ
    # -----------------------------------------------------

    for key in [
        "add_habit_type",
        "add_habit_state",
        "add_habit_name",
        "add_habit_frequency",
        "add_habit_schedule_days",
        "add_habit_difficulty",
        "add_habit_motivation",
    ]:

        context.user_data.pop(
            key,
            None
        )

    # -----------------------------------------------------
    # ГОТОВО
    # -----------------------------------------------------

    emoji = (
        "🟢"
        if habit_type == "good"
        else "🔴"
    )

    goal_text = (
        selected_goal.get(
            "title",
            "Без названия"
        )
        if selected_goal
        else
        "Для себя / без цели"
    )

    if pro_active:

        message = (
            f"{emoji} <b>Привычка добавлена.</b>\n\n"
            f"<b>{name}</b>\n\n"
            f"Периодичность: {frequency_text}\n"
            f"Сложность: {difficulty_text}\n"
            f"Цель: {goal_text}\n\n"
            "Теперь она появилась в твоей системе "
            "и будет учитываться в «Моём дне»."
        )

    else:

        message = (
            f"{emoji} <b>Привычка добавлена.</b>\n\n"
            f"<b>{name}</b>\n\n"
            f"Периодичность: {frequency_text}\n\n"
            "Теперь она появилась в твоей системе "
            "и будет учитываться в «Моём дне»."
        )

    if update.callback_query:

        await update.callback_query.message.reply_text(
            message,
            parse_mode="HTML"
        )

    elif update.message:

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

    # -----------------------------------------------------
    # ВОЗВРАТ В «МОЮ ЦЕЛЬ»
    # -----------------------------------------------------

    from handlers.goal.navigation import (
        open_habit_management
    )

    if update.callback_query:

        await open_habit_management(
            update,
            context
        )

    else:

        await open_habit_management(
            update,
            context
        )

    return True