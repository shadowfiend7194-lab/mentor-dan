from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from handlers.goal.navigation import (
    goal_back,
    open_goal_edit,
    open_habit_management,
    open_goal_add,
)

from handlers.goal.edit_goal import (
    open_goal_manage,
    edit_selected_goal,
)

from handlers.goal.habits import (
    open_habit_edit,
    open_good_habits,
    open_bad_habits,
    open_habit,
    edit_habit_frequency,
    habit_frequency_callback,
    edit_habit_name,
    open_habit_delete,
    open_habit_delete_list,
    confirm_habit_delete,
)

from handlers.goal.add_habit import (
    open_add_habit,
    add_good_habit,
    add_bad_habit,
    add_habit_frequency_callback,
    add_habit_difficulty_callback,
    add_habit_goal_callback,
)

from handlers.goal.goal_delete import (
    open_goal_delete_list,
    confirm_goal_delete,
    delete_goal,
)

from handlers.goal.pro_habit_edit import (
    edit_habit_pro_difficulty,
    set_habit_pro_difficulty,
    edit_habit_pro_motivation,
    edit_habit_pro_goal,
    set_habit_pro_goal,
)


# =========================================================
# CALLBACK-РОУТЕР «МОЯ ЦЕЛЬ»
# =========================================================

async def goal_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    print(
        "🔥 GOAL CALLBACK:",
        query.data
    )

    data = query.data

    # =====================================================
    # ПРОВЕРКА ЦЕЛИ — ДОСТИГ
    # =====================================================

    if data == "goal_review_achieved":

        await query.answer()

        context.user_data[
            "goal_review_state"
        ] = "waiting_result"

        await query.message.reply_text(
            "🏆 Отлично.\n\n"
            "Теперь расскажи, что стало для тебя "
            "доказательством, что ты действительно "
            "достиг цели.\n\n"
            "Например:\n"
            "«Мой вес 79,6 кг»\n"
            "«Сдал экзамен»\n"
            "«Теперь свободно говорю на английском»",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ Я ошибся",
                            callback_data="goal_review_back"
                        )
                    ]
                ]
            )
        )

        return

    # =====================================================
    # ОТМЕНА ПРОВЕРКИ
    # =====================================================

    if data == "goal_review_back":

        await query.answer()

        context.user_data.pop(
            "goal_review_state",
            None
        )

        await query.message.reply_text(
            "👍 Хорошо. Цель остаётся в работе."
        )

        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return

    # =====================================================
    # ПРОДОЛЖАЮ
    # =====================================================

    if data == "goal_review_continue":

        await query.answer()

        from database.goals import (
            get_main_goal,
            mark_goal_reviewed,
        )

        goal = get_main_goal(
            update.effective_user.id
        )

        if goal:

            mark_goal_reviewed(
                update.effective_user.id,
                goal["id"],
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
            )

        await query.message.reply_text(
            "💪 Хорошо.\n\n"
            "Продолжаем путь. "
            "Я спрошу тебя снова позже."
        )

        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return

    # =====================================================
    # НАЗАД К «МОЕЙ ЦЕЛИ»
    # =====================================================

    if data == "goal_back":

        await goal_back(
            update,
            context
        )

        return

    # =====================================================
    # ИЗМЕНИТЬ ЦЕЛЬ
    # =====================================================

    if data == "goal_edit":

        await open_goal_edit(
            update,
            context
        )

        return

    # =====================================================
    # УПРАВЛЕНИЕ КОНКРЕТНОЙ ЦЕЛЬЮ
    # =====================================================

    if data.startswith(
        "goal_manage_"
    ):

        await open_goal_manage(
            update,
            context
        )

        return

    # =====================================================
    # ПЕРЕИМЕНОВАТЬ КОНКРЕТНУЮ ЦЕЛЬ
    # =====================================================

    if data.startswith(
        "goal_rename_"
    ):

        await edit_selected_goal(
            update,
            context
        )

        return

    # =====================================================
    # ДОБАВИТЬ ЦЕЛЬ
    # =====================================================

    if data == "goal_add_pro":

        await open_goal_add(
            update,
            context
        )

        return

    # =====================================================
    # УДАЛЕНИЕ ЦЕЛИ — ПОДТВЕРЖДЕНИЕ
    # =====================================================

    if data.startswith(
        "goal_delete_confirm_"
    ):

        await delete_goal(
            update,
            context
        )

        return

    # =====================================================
    # УДАЛЕНИЕ ЦЕЛИ — ВЫБОР
    # =====================================================

    if data.startswith(
        "goal_delete_"
    ):

        await confirm_goal_delete(
            update,
            context
        )

        return

    # =====================================================
    # PRO — РЕДАКТИРОВАНИЕ ПРИВЫЧКИ
    # =====================================================

    if data.startswith(
        "habit_pro_locked_"
    ):

        from handlers.goal.pro_habit_edit import (
            show_pro_locked,
            get_habit_id_from_callback,
        )

        habit_id = (
            get_habit_id_from_callback(
                update
            )
        )

        if habit_id is None:
            return

        parts = data.split("_")

        feature = (
            parts[3]
            if len(parts) > 3
            else
            "difficulty"
        )

        await show_pro_locked(
            query,
            feature,
            habit_id
        )

        return

    if data.startswith(
        "habit_pro_set_difficulty_"
    ):

        await set_habit_pro_difficulty(
            update,
            context
        )

        return

    if data.startswith(
        "habit_pro_difficulty_"
    ):

        await edit_habit_pro_difficulty(
            update,
            context
        )

        return

    if data.startswith(
        "habit_pro_motivation_"
    ):

        await edit_habit_pro_motivation(
            update,
            context
        )

        return

    if data.startswith(
        "habit_pro_set_goal_"
    ):

        await set_habit_pro_goal(
            update,
            context
        )

        return

    if data.startswith(
        "habit_pro_goal_"
    ):

        await edit_habit_pro_goal(
            update,
            context
        )

        return

    # =====================================================
    # УПРАВЛЕНИЕ ПРИВЫЧКАМИ
    # =====================================================

    if data == "goal_habits":

        await open_habit_management(
            update,
            context
        )

        return

    if data == "habit_edit":

        await open_habit_edit(
            update,
            context
        )

        return

    # =====================================================
    # УДАЛЕНИЕ ПРИВЫЧКИ
    # =====================================================

    if data == "habit_delete":

        await open_habit_delete_list(
            update,
            context
        )

        return

    if data.startswith(
        "habit_delete_confirm_"
    ):

        await confirm_habit_delete(
            update,
            context
        )

        return

    if data.startswith(
        "habit_delete_"
    ):

        await open_habit_delete(
            update,
            context
        )

        return

    # =====================================================
    # ПОЛЕЗНЫЕ ПРИВЫЧКИ
    # =====================================================

    if data == "habit_edit_good":

        await open_good_habits(
            update,
            context
        )

        return

    # =====================================================
    # НЕЖЕЛАТЕЛЬНЫЕ ПРИВЫЧКИ
    # =====================================================

    if data == "habit_edit_bad":

        await open_bad_habits(
            update,
            context
        )

        return

    # =====================================================
    # ДОБАВЛЕНИЕ НОВОЙ ПРИВЫЧКИ
    # =====================================================

    if data == "habit_add_pro":

        await open_add_habit(
            update,
            context
        )

        return

    # =====================================================
    # ТИП НОВОЙ ПРИВЫЧКИ
    # =====================================================

    if data == "add_habit_good":

        await add_good_habit(
            update,
            context
        )

        return

    if data == "add_habit_bad":

        await add_bad_habit(
            update,
            context
        )

        return

    # =====================================================
    # ПЕРИОДИЧНОСТЬ
    # =====================================================

    if data in {
        "add_habit_frequency_daily",
        "add_habit_frequency_weekdays",
        "add_habit_frequency_custom",
    }:

        await add_habit_frequency_callback(
            update,
            context
        )

        return

    # =====================================================
    # СЛОЖНОСТЬ НОВОЙ ПРИВЫЧКИ
    # =====================================================

    if data.startswith(
        "add_habit_difficulty_"
    ):

        await add_habit_difficulty_callback(
            update,
            context
        )

        return
    
    # =====================================================
    # ЦЕЛЬ НОВОЙ ПРИВЫЧКИ
    # =====================================================

    if (
        data == "add_habit_goal_none"
        or data.startswith(
            "add_habit_goal_"
        )
    ):

        await add_habit_goal_callback(
            update,
            context
        )

        return
        
    # =====================================================
    # ИЗМЕНЕНИЕ НАЗВАНИЯ ПРИВЫЧКИ
    # =====================================================

    if data.startswith(
        "habit_name_"
    ):

        await edit_habit_name(
            update,
            context
        )

        return

    # =====================================================
    # ИЗМЕНЕНИЕ ПЕРИОДИЧНОСТИ
    # =====================================================

    if data.startswith(
        "habit_frequency_"
    ):

        await edit_habit_frequency(
            update,
            context
        )

        return

    if data in {
        "edit_frequency_daily",
        "edit_frequency_weekdays",
        "edit_frequency_custom",
    }:

        await habit_frequency_callback(
            update,
            context
        )

        return

    # =====================================================
    # КОНКРЕТНАЯ ПРИВЫЧКА
    # =====================================================

    if data.startswith(
        "habit_edit_"
    ):

        await open_habit(
            update,
            context
        )

        return