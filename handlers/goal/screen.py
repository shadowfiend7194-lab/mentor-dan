from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import (
    get_user_habits,
    format_frequency,
)

from database.goals import (
    get_user_goals,
    MAX_GOALS,
)

from services.subscription import (
    user_has_pro,
)

from services.dan.pro_habits import (
    get_habits_with_goals,
)


# =========================================================
# ЭКРАН «МОЯ ЦЕЛЬ»
# =========================================================

async def show_goal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    force_new=False,
):

    user_id = update.effective_user.id

    pro_active = bool(
        user_has_pro(
            user_id
        )
    )

    # =====================================================
    # ДАННЫЕ
    # =====================================================

    goals = get_user_goals(
        user_id
    )

    habits = get_user_habits(
        user_id
    )

    # =====================================================
    # PRO ДАННЫЕ
    # =====================================================

    habits_with_goals = {}

    if pro_active:

        for habit in get_habits_with_goals(
            user_id
        ):

            habits_with_goals[
                habit.get("id")
            ] = habit

    # =====================================================
    # ГРУППИРОВКА ПРИВЫЧЕК ПО ЦЕЛЯМ
    # =====================================================

    grouped = {
        goal.get("id"): []
        for goal in goals
    }

    unlinked = []

    for habit in habits:

        enriched = habits_with_goals.get(
            habit.get("id"),
            habit
        )

        goal_id = enriched.get(
            "goal_id"
        )

        if (
            pro_active
            and goal_id in grouped
        ):

            grouped[
                goal_id
            ].append(
                enriched
            )

        else:

            unlinked.append(
                enriched
            )

    # =====================================================
    # ЗАГОЛОВОК
    # =====================================================

    lines = [
        "🎯 <b>Моя цель</b>",
        "",
    ]

    # =====================================================
    # НЕТ ЦЕЛЕЙ
    # =====================================================

    if not goals:

        lines.extend(
            [
                "Пока нет активных целей.",
                "",
                "Добавь цель, чтобы Дэн мог "
                "помогать тебе двигаться "
                "к конкретному результату.",
            ]
        )

    # =====================================================
    # ЕСТЬ ЦЕЛИ
    # =====================================================

    else:

        lines.extend(
            [
                f"Активных целей: "
                f"<b>{len(goals)}</b>/{MAX_GOALS}",
                "",
                "────────────────────",
                "",
            ]
        )

        for index, goal in enumerate(
            goals
        ):

            goal_id = goal.get(
                "id"
            )

            title = (
                goal.get("title")
                or "Без названия"
            )

            marker = (
                "⭐"
                if goal.get("is_main")
                else "🎯"
            )

            # -------------------------------------------------
            # ЦЕЛЬ
            # -------------------------------------------------

            lines.append(
                f"{marker} <b>{title}</b>"
            )

            lines.append("")

            # -------------------------------------------------
            # ПРИВЫЧКИ
            # -------------------------------------------------

            if pro_active:

                linked = grouped.get(
                    goal_id,
                    []
                )

                if linked:

                    lines.append(
                        "<b>Привычки:</b>"
                    )

                    lines.append("")

                    for habit in linked:

                        habit_icon = (
                            "🟢"
                            if habit.get(
                                "habit_type"
                            ) == "good"
                            else "🔴"
                        )

                        habit_name = (
                            habit.get(
                                "name"
                            )
                            or "Без названия"
                        )

                        frequency = (
                            format_frequency(
                                habit.get(
                                    "frequency"
                                ),
                                habit.get(
                                    "schedule_days"
                                )
                            )
                        )

                        difficulty = habit.get(
                            "difficulty"
                        )

                        difficulty_text = (
                            f"{difficulty}/5"
                            if difficulty is not None
                            else "—"
                        )

                        lines.append(
                            f"{habit_icon} "
                            f"<b>{habit_name}</b>"
                        )

                        lines.append(
                            f"   Сложность: "
                            f"<b>{difficulty_text}</b>"
                        )

                        lines.append(
                            f"   {frequency}"
                        )

                        lines.append("")

                else:

                    lines.append(
                        "Привычки:"
                    )

                    lines.append(
                        "Пока нет связанных привычек."
                    )

                    lines.append("")

            else:

                lines.extend(
                    [
                        "⭐ <b>PRO</b>",
                        "Связанные привычки, сложность "
                        "и другие расширенные настройки "
                        "доступны в PRO.",
                        "",
                    ]
                )

            # -------------------------------------------------
            # РАЗДЕЛИТЕЛЬ МЕЖДУ ЦЕЛЯМИ
            # -------------------------------------------------

            if index < len(goals) - 1:

                lines.extend(
                    [
                        "────────────────────",
                        "",
                    ]
                )

    # =====================================================
    # ПРИВЫЧКИ БЕЗ ЦЕЛИ
    # =====================================================

    if pro_active and unlinked:

        lines.extend(
            [
                "────────────────────",
                "",
                "<b>Привычки без цели</b>",
                "",
            ]
        )

        for habit in unlinked:

            habit_icon = (
                "🟢"
                if habit.get(
                    "habit_type"
                ) == "good"
                else "🔴"
            )

            habit_name = (
                habit.get(
                    "name"
                )
                or "Без названия"
            )

            frequency = (
                format_frequency(
                    habit.get(
                        "frequency"
                    ),
                    habit.get(
                        "schedule_days"
                    )
                )
            )

            difficulty = (
                habit.get(
                    "difficulty"
                )
            )

            difficulty_text = (
                f"{difficulty}/5"
                if difficulty is not None
                else "—"
            )

            lines.append(
                f"{habit_icon} <b>{habit_name}</b>"
            )

            lines.append(
                f"   Сложность: "
                f"<b>{difficulty_text}</b>"
            )

            lines.append(
                f"   {frequency}"
            )

            lines.append("")

    # =====================================================
    # КНОПКИ
    # =====================================================

    keyboard = []

    # -----------------------------------------------------
    # ДОБАВИТЬ ЦЕЛЬ
    # -----------------------------------------------------

    if pro_active:

        if len(goals) < MAX_GOALS:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        "➕ Добавить цель",
                        callback_data="goal_add_pro"
                    )
                ]
            )

        else:

            lines.extend(
                [
                    "────────────────────",
                    "",
                    f"🎯 <b>Лимит целей достигнут — "
                    f"{MAX_GOALS} из {MAX_GOALS}</b>",
                    "",
                    "Не распыляйся. Лучше довести "
                    "несколько действительно важных "
                    "направлений до результата.",
                ]
            )

    else:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "➕ Добавить цель ⭐ PRO",
                    callback_data="goal_add_pro"
                )
            ]
        )

    # -----------------------------------------------------
    # ОСНОВНЫЕ КНОПКИ
    # -----------------------------------------------------

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "✏️ Изменить цель",
                    callback_data="goal_edit"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Изменить привычки",
                    callback_data="goal_habits"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Главное меню",
                    callback_data="go_menu"
                )
            ],
        ]
    )

    markup = InlineKeyboardMarkup(
        keyboard
    )

    text = "\n".join(
        lines
    )

    # =====================================================
    # РЕНДЕР
    # =====================================================

    if (
        update.callback_query
        and not force_new
    ):

        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=markup
        )