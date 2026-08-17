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
                "⬅️ Назад",
                callback_data="goal_habits"
            )
        ],
    ]

    await query.edit_message_text(
        "✏️ <b>Выбери тип привычки</b>\n\n"
        "Что хочешь изменить?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# СПИСКИ ПРИВЫЧЕК
# =========================================================

async def open_good_habits(update, context):

    await show_habits(
        update,
        context,
        "good"
    )


async def open_bad_habits(update, context):

    await show_habits(
        update,
        context,
        "bad"
    )


async def show_habits(
    update,
    context,
    habit_type
):

    query = update.callback_query

    await query.answer()

    user_id = update.effective_user.id

    habits = [
        h
        for h in get_user_habits(user_id)
        if h["habit_type"] == habit_type
    ]

    title = (
        "🟢 <b>Полезные привычки</b>\n\n"
        if habit_type == "good"
        else
        "🔴 <b>Нежелательные привычки</b>\n\n"
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
        title +
        (
            "Выбери привычку:"
            if habits
            else
            "Пока ничего нет."
        ),
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

    await query.answer()


    habit_id = int(
        query.data.replace(
            "habit_edit_",
            ""
        )
    )


    user_id = update.effective_user.id


    habit = next(
        (
            h
            for h in get_user_habits(user_id)
            if h["id"] == habit_id
        ),
        None
    )


    if not habit:
        return


    context.user_data[
        "editing_habit_id"
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
                "⬅️ Назад",
                callback_data="habit_edit"
            )
        ],
    ]


    frequency_text = format_frequency(
        habit.get("frequency"),
        habit.get("schedule_days")
    )


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
# ПЕРИОДИЧНОСТЬ
# =========================================================

async def edit_habit_frequency(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    habit_id = int(
        query.data.replace(
            "habit_frequency_",
            ""
        )
    )


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
    ]


    await query.edit_message_text(
        "📅 <b>Периодичность</b>\n\n"
        "Выбери вариант:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def habit_frequency_callback(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    data = query.data


    habit_id = context.user_data.get(
        "editing_habit_id"
    )


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

        print(
            "🔥 WAITING CUSTOM DAYS STATE:",
            context.user_data
        )

        await query.message.reply_text(
            "✏️ Напиши дни через запятую:\n\n"
            "Например:\n"
            "Пн, Ср, Пт"
        )



# =========================================================
# СОХРАНЕНИЕ СВОИХ ДНЕЙ
# =========================================================

async def save_custom_habit_frequency(
    update,
    context
):

    if context.user_data.get(
        "habit_edit_state"
    ) != "frequency_custom":

        return False


    days = parse_custom_days(
        update.message.text
    )


    if not days:

        await update.message.reply_text(
            "❌ Не смог распознать дни."
        )

        return True



    schedule_days = ",".join(
        map(str, days)
    )


    habit_id = context.user_data.get(
        "editing_habit_id"
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
        """,
        (
            "custom",
            schedule_days,
            habit_id,
            update.effective_user.id
        )
    )


    conn.commit()
    conn.close()


    context.user_data.pop(
        "habit_edit_state",
        None
    )


    await update.message.reply_text(
        "✅ Периодичность обновлена."
    )

    from handlers.goal.screen import show_goal

    await show_goal(
        update,
        context
    )

    return True



# =========================================================
# ОБНОВЛЕНИЕ
# =========================================================
async def update_frequency(
    update,
    context,
    habit_id,
    frequency,
    schedule_days
):

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
        """,
        (
            frequency,
            schedule_days,
            habit_id,
            update.effective_user.id
        )
    )

    conn.commit()
    conn.close()


    await update.effective_message.reply_text(
        "✅ Периодичность обновлена."
    )


    from handlers.goal.screen import show_goal

    await show_goal(
        update,
        context,
        force_new=True
    )

# =========================================================
# ИЗМЕНЕНИЕ НАЗВАНИЯ ПРИВЫЧКИ
# =========================================================

async def edit_habit_name(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    await query.answer()


    habit_id = int(
        query.data.replace(
            "habit_name_",
            ""
        )
    )


    context.user_data[
        "editing_habit_id"
    ] = habit_id


    context.user_data[
        "habit_edit_state"
    ] = "name"


    await query.message.reply_text(
        "✏️ <b>Новое название привычки</b>\n\n"
        "Напиши новое название:",
        parse_mode="HTML"
    )

# =========================================================
# СОХРАНЕНИЕ НАЗВАНИЯ ПРИВЫЧКИ
# =========================================================

async def save_habit_name(
    update,
    context
):

    if not update.message:
        return False


    if context.user_data.get(
        "habit_edit_state"
    ) != "name":

        return False


    name = update.message.text.strip()


    if not name:
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

        SET name = ?

        WHERE id = ?

        AND user_id = ?

        """,
        (
            name,
            habit_id,
            update.effective_user.id,
        )
    )


    conn.commit()
    conn.close()


    context.user_data.pop(
        "habit_edit_state",
        None
    )


    await update.message.reply_text(
        "✅ Название привычки обновлено."
    )


    from handlers.goal.screen import show_goal

    await show_goal(
        update,
        context
    )


    return True