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
)

from handlers.goal.edit_goal import (
    edit_current_goal,
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
    # ОТМЕНА ПОДТВЕРЖДЕНИЯ ДОСТИЖЕНИЯ
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
    # ПРОВЕРКА ЦЕЛИ — ПРОДОЛЖАЮ
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
    # ИЗМЕНИТЬ ТЕКУЩУЮ ЦЕЛЬ
    # =====================================================

    if data == "goal_edit_current":

        await edit_current_goal(
            update,
            context
        )

        return


    # =====================================================
    # PRO — ДОБАВИТЬ ЦЕЛЬ
    # =====================================================

    if data == "goal_add_pro":

        await query.answer()

        await query.message.reply_text(
            "⭐ <b>Эта возможность доступна в PRO</b>\n\n"
            "С PRO ты сможешь добавлять дополнительные цели "
            "и работать сразу над несколькими направлениями.\n\n"
            "🚀 Скоро.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Назад",
                            callback_data="goal_edit"
                        )
                    ]
                ]
            )
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


    # =====================================================
    # ОТКРЫТЬ УПРАВЛЕНИЕ ПРИВЫЧКАМИ
    # =====================================================

    if data == "habit_edit":

        await open_habit_edit(
            update,
            context
        )

        return


    # =====================================================
    # УДАЛЕНИЕ ПРИВЫЧКИ — СПИСОК
    # =====================================================

    if data == "habit_delete":

        await open_habit_delete_list(
            update,
            context
        )

        return


    # =====================================================
    # УДАЛЕНИЕ ПРИВЫЧКИ — ПОДТВЕРЖДЕНИЕ
    # =====================================================

    if data.startswith(
        "habit_delete_confirm_"
    ):

        await confirm_habit_delete(
            update,
            context
        )

        return


    # =====================================================
    # УДАЛЕНИЕ ПРИВЫЧКИ — ВЫБОР ПРИВЫЧКИ
    # =====================================================

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
    # ВЫБОР ТИПА НОВОЙ ПРИВЫЧКИ
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
    # ПЕРИОДИЧНОСТЬ НОВОЙ ПРИВЫЧКИ
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
    # ИЗМЕНЕНИЕ ПЕРИОДИЧНОСТИ ПРИВЫЧКИ
    # =====================================================

    if data.startswith(
        "habit_frequency_"
    ):

        await edit_habit_frequency(
            update,
            context
        )

        return


    # =====================================================
    # ВЫБОР НОВОЙ ПЕРИОДИЧНОСТИ ПРИ РЕДАКТИРОВАНИИ
    # =====================================================

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
    # ВЫБОР КОНКРЕТНОЙ ПРИВЫЧКИ
    # =====================================================

    if data.startswith(
        "habit_edit_"
    ):

        await open_habit(
            update,
            context
        )

        return

