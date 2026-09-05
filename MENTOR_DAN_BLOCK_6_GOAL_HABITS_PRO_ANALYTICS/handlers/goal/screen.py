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
    FREE_MAX_GOALS,
    PRO_MAX_GOALS,
)

from services.subscription import (
    user_has_pro,
)

from services.dan.pro_habits import (
    get_habits_with_goals,
)


DIFFICULTY_LABELS = {
    1: "Очень легко",
    2: "Легко",
    3: "Средне",
    4: "Сложно",
    5: "Очень сложно",
}


def difficulty_label(value):
    try:
        return DIFFICULTY_LABELS.get(int(value), "—")
    except (TypeError, ValueError):
        return "—"


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

    max_goals = (
        PRO_MAX_GOALS
        if pro_active
        else FREE_MAX_GOALS
    )

    # =====================================================
    # ДАННЫЕ
    # =====================================================

    all_goals = get_user_goals(
        user_id
    )

    # Одноразовая защита от старого бага: кнопка «🎯 Моя цель»
    # могла попасть в обработчик онбординга и сохраниться как цель.
    # Удаляем только явно распознаваемую служебную цель, если у пользователя
    # уже есть другие реальные цели. Намеренные пользовательские цели не трогаем,
    # если это единственная цель.
    phantom_ids = [
        goal.get("id")
        for goal in all_goals
        if str(goal.get("title") or "").strip() in {
            "🎯 Моя цель",
            "⭐ Моя цель",
            "🎯 🎯 Моя цель",
        }
    ]
    real_goals = [goal for goal in all_goals if goal.get("id") not in phantom_ids]
    if phantom_ids and real_goals:
        from database.goals import deactivate_goal
        for phantom_id in phantom_ids:
            deactivate_goal(user_id, phantom_id)
        all_goals = get_user_goals(user_id)

    frozen_goals_count = sum(
        1
        for goal in all_goals
        if goal.get("pro_status") == "frozen"
    )

    if pro_active:
        goals = all_goals
    else:
        goals = [
            goal
            for goal in all_goals
            if goal.get("pro_status") != "frozen"
        ]

    habits = get_user_habits(
        user_id
    )

    frozen_habits_count = sum(
        1
        for habit in habits
        if habit.get("pro_status") == "frozen"
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
                f"<b>{len(goals)}</b>/{max_goals}",
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
                            f"<b>{difficulty_label(difficulty)}</b>"
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

                # В FREE показываем обычные активные привычки,
                # но без PRO-параметров и без раскрытия связей.
                # Это позволяет пользователю понимать, какие
                # привычки у него сейчас реально активны.
                if index == 0:

                    free_habits = [
                        habit
                        for habit in habits
                        if habit.get("pro_status") != "frozen"
                    ]

                    if free_habits:

                        lines.extend(
                            [
                                "<b>Привычки:</b>",
                                "",
                            ]
                        )

                        for habit in free_habits:

                            habit_icon = (
                                "🟢"
                                if habit.get("habit_type") == "good"
                                else "🔴"
                            )

                            habit_name = (
                                habit.get("name")
                                or "Без названия"
                            )

                            frequency = format_frequency(
                                habit.get("frequency"),
                                habit.get("schedule_days")
                            )

                            lines.append(
                                f"{habit_icon} <b>{habit_name}</b>"
                            )
                            lines.append(
                                f"   {frequency}"
                            )
                            lines.append("")

                    else:

                        lines.extend(
                            [
                                "<b>Привычки:</b>",
                                "Пока нет активных привычек.",
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

    if (not pro_active) and frozen_habits_count:

        lines.extend(
            [
                "────────────────────",
                "",
                f"🔒 <b>{frozen_habits_count} привычки заморожены после окончания PRO.</b>",
                "Вернуть их и снова работать с ними можно после продления PRO.",
                "",
            ]
        )

    if (not pro_active) and frozen_goals_count:

        lines.extend(
            [
                "────────────────────",
                "",
                f"🔒 <b>{frozen_goals_count} целей заморожены после окончания PRO.</b>",
                "Вернуть их и снова работать с ними можно после продления PRO.",
                "",
            ]
        )

    # =====================================================
    # КНОПКИ
    # =====================================================

    keyboard = []

    # -----------------------------------------------------
    # ДОБАВИТЬ ЦЕЛЬ
    # -----------------------------------------------------

    if pro_active:

        if len(goals) < max_goals:

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
                    f"{max_goals} из {max_goals}</b>",
                    "",
                    "Не распыляйся. Лучше довести "
                    "несколько действительно важных "
                    "направлений до результата.",
                ]
            )

    else:

        if len(goals) < FREE_MAX_GOALS:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        "➕ Добавить цель",
                        callback_data="goal_add_pro"
                    )
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