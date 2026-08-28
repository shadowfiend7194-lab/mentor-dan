from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import (
    get_user_habits,
    parse_custom_days,
    format_frequency,
    format_custom_days,
    mark_habit_removed,
)

from database.connection import get_connection


# =========================================================
# ВЫБОР ТИПА ПРИВЫЧКИ
# =========================================================

async def open_habit_edit(
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
                "🟢 Полезные привычки",
                callback_data="habit_edit_good"
            )
        ],
        [
            InlineKeyboardButton(
                "🔴 Нежелательные привычки",
                callback_data="habit_edit_bad"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить привычку",
                callback_data="habit_delete"
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
        "⚙️ <b>Управление привычками</b>\n\n"
        "Здесь можно изменить или удалить "
        "любую активную привычку.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ВЫБОР ПРИВЫЧКИ ДЛЯ УДАЛЕНИЯ
# =========================================================

async def open_habit_delete_list(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    habits = get_user_habits(
        user_id
    )

    keyboard = []

    for habit in habits:

        icon = (
            "🟢"
            if habit["habit_type"] == "good"
            else
            "🔴"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {habit['name']}",
                    callback_data=f"habit_delete_{habit['id']}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="habit_edit"
            )
        ]
    )

    await query.edit_message_text(
        "🗑 <b>Удаление привычки</b>\n\n"
        "Выбери привычку, которую хочешь удалить:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

# =========================================================
# СПИСОК ПОЛЕЗНЫХ ПРИВЫЧЕК
# =========================================================

async def open_good_habits(
    update,
    context
):

    await show_habits(
        update,
        context,
        "good"
    )


# =========================================================
# СПИСОК НЕЖЕЛАТЕЛЬНЫХ ПРИВЫЧЕК
# =========================================================

async def open_bad_habits(
    update,
    context
):

    await show_habits(
        update,
        context,
        "bad"
    )


# =========================================================
# СПИСОК ПРИВЫЧЕК
# =========================================================

async def show_habits(
    update,
    context,
    habit_type
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    habits = [
        h
        for h in get_user_habits(user_id)
        if h["habit_type"] == habit_type
    ]

    if habit_type == "good":

        title = (
            "🟢 <b>Полезные привычки</b>\n\n"
            "Выбери привычку:"
        )

    else:

        title = (
            "🔴 <b>Нежелательные привычки</b>\n\n"
            "Выбери привычку:"
        )

    keyboard = []

    for habit in habits:

        keyboard.append(
            [
                InlineKeyboardButton(
                    habit["name"],
                    callback_data=f"habit_edit_{habit['id']}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="habit_edit"
            )
        ]
    )

    await query.edit_message_text(
        title
        if habits
        else
        title + "\n\nПока здесь ничего нет.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# КАРТОЧКА ПРИВЫЧКИ
# =========================================================

async def open_habit(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        habit_id = int(
            query.data.replace(
                "habit_edit_",
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

        await query.message.reply_text(
            "❌ Привычка не найдена."
        )

        return

    context.user_data[
        "editing_habit_id"
    ] = habit_id

    context.user_data[
        "editing_habit_type"
    ] = habit["habit_type"]

    icon = (
        "🟢"
        if habit["habit_type"] == "good"
        else
        "🔴"
    )

    frequency_text = format_frequency(
        habit.get("frequency"),
        habit.get("schedule_days")
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "✏️ Название",
                callback_data=f"habit_name_{habit_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "📅 Периодичность",
                callback_data=f"habit_frequency_{habit_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "🗑 Удалить привычку",
                callback_data=f"habit_delete_{habit_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=(
                    "habit_edit_good"
                    if habit["habit_type"] == "good"
                    else
                    "habit_edit_bad"
                )
            )
        ],

    ]

    text = (
        f"{icon} <b>{habit['name']}</b>\n\n"
        f"📅 {frequency_text}\n\n"
        "Что хочешь изменить?"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# =========================================================

async def open_habit_delete(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        habit_id = int(
            query.data.replace(
                "habit_delete_",
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

        await query.message.reply_text(
            "❌ Привычка уже не найдена."
        )

        return

    context.user_data[
        "deleting_habit_id"
    ] = habit_id

    icon = (
        "🟢"
        if habit["habit_type"] == "good"
        else
        "🔴"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🗑 Да, удалить",
                callback_data=f"habit_delete_confirm_{habit_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "↩️ Отмена",
                callback_data=f"habit_edit_{habit_id}"
            )
        ],

    ]

    await query.edit_message_text(
        f"{icon} <b>{habit['name']}</b>\n\n"
        "Удалить эту привычку?\n\n"
        "Она перестанет отображаться в твоём дне "
        "и больше не будет учитываться как активная.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ПОДТВЕРЖДЁННОЕ УДАЛЕНИЕ
# =========================================================

async def confirm_habit_delete(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        habit_id = int(
            query.data.replace(
                "habit_delete_confirm_",
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

        await query.edit_message_text(
            "❌ Привычка уже удалена."
        )

        return

    habit_name = habit["name"]

    habit_type = habit["habit_type"]

    mark_habit_removed(
        user_id,
        habit_id
    )

    context.user_data.pop(
        "editing_habit_id",
        None
    )

    context.user_data.pop(
        "deleting_habit_id",
        None
    )

    await query.edit_message_text(
        f"🗑 <b>Привычка удалена</b>\n\n"
        f"«{habit_name}» больше не будет отображаться "
        f"в твоём дне.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ К привычкам",
                        callback_data="habit_edit"
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
    )


# =========================================================
# ПЕРИОДИЧНОСТЬ
# =========================================================

async def edit_habit_frequency(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        habit_id = int(
            query.data.replace(
                "habit_frequency_",
                ""
            )
        )

    except ValueError:

        return

    context.user_data[
        "editing_habit_id"
    ] = habit_id

    keyboard = [

        [
            InlineKeyboardButton(
                "📅 Каждый день",
                callback_data="edit_frequency_daily"
            )
        ],

        [
            InlineKeyboardButton(
                "🗓️ Пн–Пт",
                callback_data="edit_frequency_weekdays"
            )
        ],

        [
            InlineKeyboardButton(
                "✏️ Свои дни",
                callback_data="edit_frequency_custom"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=f"habit_edit_{habit_id}"
            )
        ],

    ]

    await query.edit_message_text(
        "📅 <b>Периодичность</b>\n\n"
        "Выбери вариант:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# СОХРАНЕНИЕ ПЕРИОДИЧНОСТИ
# =========================================================

async def habit_frequency_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data

    habit_id = context.user_data.get(
        "editing_habit_id"
    )

    if not habit_id:
        return

    if data == "edit_frequency_daily":

        await update_frequency(
            update,
            context,
            habit_id,
            "daily",
            None
        )

    elif data == "edit_frequency_weekdays":

        await update_frequency(
            update,
            context,
            habit_id,
            "weekdays",
            None
        )

    elif data == "edit_frequency_custom":

        context.user_data[
            "habit_edit_state"
        ] = "frequency_custom"

        await query.message.reply_text(
            "✏️ <b>Свои дни</b>\n\n"
            "Напиши дни через запятую.\n\n"
            "Например:\n"
            "Пн, Ср, Пт",
            parse_mode="HTML"
        )


# =========================================================
# ОБНОВЛЕНИЕ ПЕРИОДИЧНОСТИ
# =========================================================

async def update_frequency(
    update,
    context,
    habit_id,
    frequency,
    schedule_days
):

    user_id = update.effective_user.id

    if frequency == "custom":

        parsed = parse_custom_days(
            schedule_days
        )

        if not parsed:

            await update.effective_message.reply_text(
                "❌ Не удалось распознать дни.\n\n"
                "Напиши, например:\n"
                "Пн, Ср, Пт"
            )

            return

        schedule_days = ",".join(
            map(str, parsed)
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET
            frequency = ?,
            schedule_days = ?

        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            frequency,
            schedule_days,
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

    await update.effective_message.reply_text(
        "✅ <b>Периодичность обновлена.</b>\n\n"
        "Привычка сохранена.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ К привычке",
                        callback_data=f"habit_edit_{habit_id}"
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
    )


# =========================================================
# ИЗМЕНЕНИЕ НАЗВАНИЯ
# =========================================================

async def edit_habit_name(
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
                "habit_name_",
                ""
            )
        )

    except ValueError:

        return

    context.user_data[
        "editing_habit_id"
    ] = habit_id

    context.user_data[
        "habit_edit_state"
    ] = "name"

    await query.message.reply_text(
        "✏️ <b>Новое название</b>\n\n"
        "Напиши новое название привычки.",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНЕНИЕ НОВОГО НАЗВАНИЯ ПРИВЫЧКИ
# =========================================================

async def save_habit_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    habit_id = context.user_data.get(
        "editing_habit_id"
    )

    if not habit_id:
        return False

    new_name = update.message.text.strip()

    if not new_name:
        await update.message.reply_text(
            "❌ Название не может быть пустым.\n\n"
            "Напиши новое название привычки."
        )
        return True

    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET name = ?

        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            new_name,
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
        f"✏️ <b>Привычка обновлена</b>\n\n"
        f"Теперь она называется:\n"
        f"<b>«{new_name}»</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ К привычке",
                        callback_data=f"habit_edit_{habit_id}"
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
    )

    return True


# =========================================================
# СОХРАНЕНИЕ СВОИХ ДНЕЙ ПРИВЫЧКИ
# =========================================================

async def save_custom_habit_frequency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    habit_id = context.user_data.get(
        "editing_habit_id"
    )

    if not habit_id:
        return False

    text = update.message.text.strip()

    parsed = parse_custom_days(
        text
    )

    if not parsed:

        await update.message.reply_text(
            "❌ Не удалось распознать дни.\n\n"
            "Напиши их через запятую.\n\n"
            "Например:\n"
            "Пн, Ср, Пт"
        )

        return True

    schedule_days = ",".join(
        map(str, parsed)
    )

    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE habits

        SET
            frequency = 'custom',
            schedule_days = ?

        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            schedule_days,
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

    days_text = format_custom_days(
        schedule_days
    )

    await update.message.reply_text(
        f"📅 <b>Периодичность обновлена</b>\n\n"
        f"Привычка теперь выполняется:\n"
        f"<b>{days_text}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ К привычке",
                        callback_data=f"habit_edit_{habit_id}"
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
    )

    return True