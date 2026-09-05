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

from services.subscription import (
    user_has_pro,
    get_user_plan,
)


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
                "⬅️ Назад",
                callback_data="goal_habits"
            )
        ],
    ]

    await query.edit_message_text(
        "✏️ <b>Выбери тип привычки</b>\n\n"
        "Что хочешь изменить?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# СПИСКИ ПРИВЫЧЕК
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


async def open_bad_habits(
    update,
    context
):

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

    if not query:
        return

    await query.answer()

    user_id = update.effective_user.id

    pro_active = bool(
        user_has_pro(user_id)
    )

    all_habits = get_user_habits(
        user_id
    )

    # -----------------------------------------------------
    # FREE:
    # замороженные привычки не показываем
    #
    # PRO:
    # показываем всё
    # -----------------------------------------------------

    habits = [
        habit
        for habit in all_habits
        if habit["habit_type"] == habit_type
        and (
            pro_active
            or habit.get("pro_status") != "frozen"
        )
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
                    callback_data=(
                        f"habit_edit_{habit['id']}"
                    )
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
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# КАРТОЧКА КОНКРЕТНОЙ ПРИВЫЧКИ
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

    # -----------------------------------------------------
    # ЗАЩИТА ЗАМОРОЖЕННОЙ ПРИВЫЧКИ
    # -----------------------------------------------------

    if (
        habit.get("pro_status") == "frozen"
        and not user_has_pro(user_id)
    ):

        await query.edit_message_text(
            "🔒 <b>Привычка заморожена</b>\n\n"
            "Она была создана или расширена во время PRO.\n\n"
            "Чтобы снова работать с этой привычкой, "
            "верни PRO.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⭐ Вернуть PRO",
                            callback_data="pro_subscribe"
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
            )
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

    # =====================================================
    # ПЕРИОДИЧНОСТЬ
    # =====================================================

    frequency_text = format_frequency(
        habit.get("frequency"),
        habit.get("schedule_days")
    )

    # =====================================================
    # PRO ДАННЫЕ
    # =====================================================

    plan = get_user_plan(
        user_id
    )

    difficulty = habit.get(
        "difficulty"
    )

    motivation = habit.get(
        "motivation"
    )

    goal_id = habit.get(
        "goal_id"
    )

    goal_title = None

    # -----------------------------------------------------
    # НАХОДИМ ЦЕЛЬ ПО goal_id
    # -----------------------------------------------------

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

            goal_title = None

    # =====================================================
    # ТЕКСТ КАРТОЧКИ
    # =====================================================

    text = (
        f"{icon} <b>{habit['name']}</b>\n\n"
        f"📅 <b>Периодичность:</b> "
        f"{frequency_text}\n"
    )

    # -----------------------------------------------------
    # PRO ИНФОРМАЦИЯ
    # -----------------------------------------------------

    if plan == "pro":

        # СЛОЖНОСТЬ

        if difficulty is not None:

            text += (
                f"🔥 <b>Сложность:</b> "
                f"{difficulty}/5\n"
            )

        else:

            text += (
                "🔥 <b>Сложность:</b> "
                "не указана\n"
            )

        # ЦЕЛЬ

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

        # МОТИВАЦИЯ

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

    # =====================================================
    # ЧТО ИЗМЕНИТЬ
    # =====================================================

    text += (
        "\n<b>Что хочешь изменить?</b>"
    )

    # =====================================================
    # КНОПКИ
    # =====================================================

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
    ]

    # -----------------------------------------------------
    # PRO КНОПКИ
    # -----------------------------------------------------

    if plan == "pro":

        keyboard.extend(
            [
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
            ]
        )

    # -----------------------------------------------------
    # НАЗАД
    # -----------------------------------------------------

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=(
                    "habit_edit_good"
                    if habit["habit_type"] == "good"
                    else "habit_edit_bad"
                )
            )
        ]
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
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
                callback_data=(
                    f"habit_edit_{habit_id}"
                )
            )
        ],
    ]

    await query.edit_message_text(
        "📅 <b>Периодичность</b>\n\n"
        "Выбери вариант:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ВЫБОР ПЕРИОДИЧНОСТИ
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

        context.user_data.pop("habit_edit_state", None)

        await update_frequency(
            update,
            context,
            habit_id,
            "daily",
            None
        )

    elif data == "edit_frequency_weekdays":

        context.user_data.pop("habit_edit_state", None)

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

    if not update.message:

        return False

    days = parse_custom_days(
        update.message.text
    )

    if not days:

        await update.message.reply_text(
            "❌ Не смог распознать дни.\n\n"
            "Напиши, например:\n"
            "Пн, Ср, Пт"
        )

        return True

    schedule_days = ",".join(
        map(str, days)
    )

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

        SET
            frequency = ?,
            schedule_days = ?

        WHERE id = ?
        AND user_id = ?
        AND active = 1
        """,
        (
            "custom",
            schedule_days,
            habit_id,
            update.effective_user.id
        )
    )

    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()

    context.user_data.pop(
        "habit_edit_state",
        None
    )

    if not changed:
        await update.message.reply_text(
            "❌ Не получилось обновить периодичность. Привычка могла быть удалена или изменена."
        )
        return True

    await update.message.reply_text(
        "✅ <b>Периодичность обновлена.</b>",
        parse_mode="HTML"
    )

    # После текстового ввода сразу возвращаем пользователя
    # в карточку той же привычки.
    from handlers.goal.pro_habit_edit import show_habit_card_after_text
    await show_habit_card_after_text(
        update,
        context,
        habit_id,
    )

    return True


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
            update.effective_user.id
        )
    )

    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not changed:
        await update.effective_message.reply_text(
            "❌ Не получилось обновить периодичность."
        )
        return

    context.user_data.pop("habit_edit_state", None)

    # Если изменение произошло по inline-кнопке, обновляем ту же карточку.
    if update.callback_query:
        try:
            await update.callback_query.answer("📅 Периодичность обновлена.")
        except Exception:
            pass
        from handlers.goal.habits import open_habit
        await open_habit(update, context)
        return

    await update.effective_message.reply_text(
        "✅ <b>Периодичность обновлена.</b>",
        parse_mode="HTML"
    )

    from handlers.goal.pro_habit_edit import show_habit_card_after_text
    await show_habit_card_after_text(
        update,
        context,
        habit_id,
    )


# =========================================================
# ИЗМЕНЕНИЕ НАЗВАНИЯ
# =========================================================

async def edit_habit_name(
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
        "✏️ <b>Новое название привычки</b>\n\n"
        "Напиши новое название:",
        parse_mode="HTML"
    )


# =========================================================
# СОХРАНЕНИЕ НАЗВАНИЯ
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

        await update.message.reply_text(
            "Название не может быть пустым."
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
        "✅ <b>Название привычки обновлено.</b>",
        parse_mode="HTML"
    )

    from handlers.goal.screen import (
        show_goal
    )

    await show_goal(
        update,
        context
    )

    return True