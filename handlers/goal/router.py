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
    save_custom_habit_frequency,
    edit_habit_name,
    save_habit_name,
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

    data = query.data

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
    # ИЗМЕНИТЬ ТЕКУЩУЮ ПРИВЫЧКУ
    # =====================================================

    if data == "habit_edit":

        await open_habit_edit(
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
    # конкретная привычка
    # =====================================================

    if data.startswith("habit_edit_"):

        await open_habit(
            update,
            context
        )

        return


    # =====================================================
    # PRO — ДОБАВИТЬ ПРИВЫЧКУ
    # =====================================================

    if data == "habit_add_pro":

        await query.answer()

        await query.message.reply_text(
            "⭐ <b>Эта возможность доступна в PRO</b>\n\n"
            "С PRO ты сможешь добавлять дополнительные "
            "полезные и нежелательные привычки.\n\n"
            "🚀 Скоро.",
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

        return

    

    # =====================================================
    # ИЗМЕНЕНИЕ НАЗВАНИЯ
    # =====================================================

    if data.startswith("habit_name_"):

        await edit_habit_name(
            update,
            context
        )

        return

    # =====================================================
    # ИЗМЕНЕНИЕ ПЕРИОДИЧНОСТИ
    # =====================================================

    if data.startswith("habit_frequency_"):

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
        