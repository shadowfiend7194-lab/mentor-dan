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

    habits = get_user_habits(user_id)

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
            "🟢 до <b>5 полезных</b> привычек\n"
            "🔴 до <b>5 нежелательных</b> привычек\n\n"
            "<b>Стабильность важнее количества. 💪</b>",
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

    good_count, _ = get_habit_counts(
        update.effective_user.id
    )

    if good_count >= 5:
        await show_habit_limit(update, context)
        return

    await query.answer()

    context.user_data["add_habit_type"] = "good"
    context.user_data["add_habit_state"] = "name"

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

    _, bad_count = get_habit_counts(
        update.effective_user.id
    )

    if bad_count >= 5:
        await show_habit_limit(update, context)
        return

    await query.answer()

    context.user_data["add_habit_type"] = "bad"
    context.user_data["add_habit_state"] = "name"

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

    context.user_data["add_habit_name"] = name
    context.user_data["add_habit_state"] = "frequency"

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
        reply_markup=InlineKeyboardMarkup(keyboard)
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

        context.user_data["add_habit_frequency"] = "daily"
        context.user_data["add_habit_schedule_days"] = None

    elif data == "add_habit_frequency_weekdays":

        context.user_data["add_habit_frequency"] = "weekdays"
        context.user_data["add_habit_schedule_days"] = None

    elif data == "add_habit_frequency_custom":

        context.user_data["add_habit_frequency"] = "custom"
        context.user_data["add_habit_state"] = "frequency_custom"

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

    context.user_data["add_habit_state"] = "difficulty"

    await show_habit_difficulty(
        query.message,
        context
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

    parsed = parse_custom_days(text)

    if not parsed:

        await update.message.reply_text(
            "⚠️ Не смог распознать дни.\n\n"
            "Напиши их через запятую.\n"
            "Например: <b>Пн, Вт, Чт</b>",
            parse_mode="HTML"
        )

        return True

    schedule_days = ",".join(
        map(str, parsed)
    )

    context.user_data[
        "add_habit_schedule_days"
    ] = schedule_days

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

    return True


# =========================================================
# СЛОЖНОСТЬ 1–5
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
        reply_markup=InlineKeyboardMarkup(keyboard)
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

    difficulty = int(
        query.data.split("_")[-1]
    )

    context.user_data[
        "add_habit_difficulty"
    ] = difficulty

    context.user_data[
        "add_habit_state"
    ] = "motivation"

    await query.message.reply_text(
        "💭 <b>Зачем тебе эта привычка?</b>\n\n"
        "Напиши своими словами, почему ты хочешь "
        "её сформировать или от неё избавиться.\n\n"
        "Например:\n"
        "«Хочу больше энергии и лучше себя чувствовать»\n"
        "«Хочу меньше зависать в телефоне»\n"
        "«Хочу наконец-то привести режим в порядок»",
        parse_mode="HTML"
    )


# =========================================================
# МОТИВАЦИЯ
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
            "Напиши пару слов о том, зачем тебе эта привычка."
        )
        return True

    context.user_data[
        "add_habit_motivation"
    ] = motivation

    # -----------------------------------------------------
    # СОЗДАЁМ ПРИВЫЧКУ
    # -----------------------------------------------------

    habit_id = create_habit(
        user_id=update.effective_user.id,
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
        difficulty=context.user_data.get(
            "add_habit_difficulty"
        ),
        motivation=context.user_data.get(
            "add_habit_motivation"
        )
    )

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

    frequency_text = format_frequency(
        frequency,
        schedule_days
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

    await update.message.reply_text(
        f"{emoji} <b>Привычка добавлена.</b>\n\n"
        f"<b>{name}</b>\n"
        f"📅 {frequency_text}\n\n"
        "Теперь она появилась в твоей системе "
        "и будет учитываться в «Моём дне».\n\n"
        "Не пытайся сделать всё идеально. "
        "Главное — начать выполнять.",
        parse_mode="HTML"
    )

    # -----------------------------------------------------
    # ВОЗВРАТ В «МОЮ ЦЕЛЬ»
    # -----------------------------------------------------

    from handlers.goal.navigation import (
        open_habit_management
    )

    await open_habit_management(
        update,
        context
    )

    return True

