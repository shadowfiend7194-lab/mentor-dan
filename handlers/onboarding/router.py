from telegram import Update
from telegram.ext import ContextTypes

from handlers.onboarding.intro import (
    start_intro,
    why_intro,
    back_to_start,
)

from handlers.onboarding.profile import (
    handle_name,
    handle_age_callback,
)

from handlers.onboarding.goals import (
    handle_main_goal,
)

from handlers.onboarding.habits import (
    handle_good_habit,
    handle_good_habit_frequency_callback,
    handle_good_habit_custom_frequency,
    handle_bad_habit_callback,
    handle_bad_habit_name,
    handle_bad_habit_frequency_callback,
    handle_bad_habit_custom_frequency,
)

from handlers.onboarding.oath import (
    accept_oath,
)

from handlers.onboarding.sleep import (
    handle_wake_time,
    handle_sleep_time,
)

from handlers.menu import (
    menu_text,
    show_menu,
)

from handlers.day.morning import (
    morning_answer,
)

from handlers.day.evening import (
    handle_evening_text,
)


from handlers.goal.edit_goal import (
    save_edited_goal,
)

from handlers.goal.habits import (
    save_habit_name,
    save_custom_habit_frequency,
)


# =========================================================
# CALLBACK-КНОПКИ
# =========================================================

async def onboarding_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    data = query.data

    # =====================================================
    # СТАРТОВЫЕ КНОПКИ
    # =====================================================

    if data == "start_intro":

        await start_intro(
            update,
            context
        )

        return

    if data == "why_intro":

        await why_intro(
            update,
            context
        )

        return

    if data == "back_to_start":

        await back_to_start(
            update,
            context
        )

        return

    # =====================================================
    # ВОЗРАСТ
    # =====================================================

    if data in {
        "age_under_18",
        "age_18_25",
        "age_26_35",
        "age_35_plus",
    }:

        await handle_age_callback(
            update,
            context
        )

        return

    # =====================================================
    # ХОРОШАЯ ПРИВЫЧКА — ПЕРИОДИЧНОСТЬ
    # =====================================================

    if data in {
        "good_frequency_daily",
        "good_frequency_weekdays",
        "good_frequency_custom",
    }:

        await handle_good_habit_frequency_callback(
            update,
            context
        )

        return

    # =====================================================
    # ПЛОХАЯ ПРИВЫЧКА — ЕСТЬ / НЕТ
    # =====================================================

    if data in {
        "bad_habit_yes",
        "bad_habit_no",
    }:

        await handle_bad_habit_callback(
            update,
            context
        )

        return

    # =====================================================
    # ПЛОХАЯ ПРИВЫЧКА — ПЕРИОДИЧНОСТЬ
    # =====================================================

    if data in {
        "bad_frequency_daily",
        "bad_frequency_weekdays",
        "bad_frequency_custom",
    }:

        await handle_bad_habit_frequency_callback(
            update,
            context
        )

        return

    # =====================================================
    # КЛЯТВА
    # =====================================================

    if data == "oath_accept":

        await accept_oath(
            update,
            context
        )

        return

    # =====================================================
    # ГЛАВНОЕ МЕНЮ ПОСЛЕ ОНБОРДИНГА
    # =====================================================

    if data == "open_main_menu":

        await query.answer()

        context.user_data[
            "onboarding_step"
        ] = "completed"

        await show_menu(
            update,
            context
        )

        return


# =========================================================
# ТЕКСТОВЫЕ СООБЩЕНИЯ
# =========================================================

async def text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    # =====================================================
    # УТРЕННИЙ ЧЕК-ИН
    # =====================================================

    if context.user_data.get(
        "checkin_type"
    ) == "morning":

        await morning_answer(
            update,
            context
        )

        return


    # =====================================================
    # ВЕЧЕРНИЙ ЧЕК-ИН
    # =====================================================

    if context.user_data.get(
        "checkin_type"
    ) == "evening":

        handled = await handle_evening_text(
            update,
            context
        )

        if handled:
            return


    # =====================================================
    # ИЗМЕНЕНИЕ ЦЕЛИ
    # =====================================================

    if context.user_data.get(
        "goal_edit_state"
    ) == "waiting":

        handled = await save_edited_goal(
            update,
            context
        )

        if handled:
            return


    # =====================================================
    # ИЗМЕНЕНИЕ НАЗВАНИЯ ПРИВЫЧКИ
    # =====================================================

    if context.user_data.get(
        "habit_edit_state"
    ) == "name":

        handled = await save_habit_name(
            update,
            context
        )

        if handled:
            return


    # =====================================================
    # СВОИ ДНИ ПРИВЫЧКИ
    # =====================================================

    if context.user_data.get(
        "habit_edit_state"
    ) == "frequency_custom":

        print(
            "🔥 SAVE CUSTOM DAYS:",
            update.message.text
        )

        handled = await save_custom_habit_frequency(
            update,
            context
        )

        if handled:
            return


    step = context.user_data.get(
        "onboarding_step"
    )


    # =====================================================
    # ЕСЛИ ПОЛЬЗОВАТЕЛЬ УЖЕ ПРОШЁЛ ОНБОРДИНГ
    # =====================================================

    if step == "completed":

        await menu_text(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — ИМЯ
    # =====================================================

    if step == "name":

        await handle_name(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — ГЛАВНАЯ ЦЕЛЬ
    # =====================================================

    if step == "main_goal":

        await handle_main_goal(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — ПОЛЕЗНАЯ ПРИВЫЧКА
    # =====================================================

    if step == "good_habit":

        await handle_good_habit(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — СВОИ ДНИ ПОЛЕЗНОЙ ПРИВЫЧКИ
    # =====================================================

    if step == "good_habit_custom_frequency":

        await handle_good_habit_custom_frequency(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — НАЗВАНИЕ ПЛОХОЙ ПРИВЫЧКИ
    # =====================================================

    if step == "bad_habit_name":

        await handle_bad_habit_name(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — СВОИ ДНИ ПЛОХОЙ ПРИВЫЧКИ
    # =====================================================

    if step == "bad_habit_custom_frequency":

        await handle_bad_habit_custom_frequency(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — ВРЕМЯ ПОДЪЁМА
    # =====================================================

    if step == "wake_time":

        await handle_wake_time(
            update,
            context
        )

        return


    # =====================================================
    # ОНБОРДИНГ — ВРЕМЯ СНА
    # =====================================================

    if step == "sleep_time":

        await handle_sleep_time(
            update,
            context
        )

        return


    # =====================================================
    # ЕСЛИ НИЧЕГО НЕ СРАБОТАЛО
    # =====================================================

    await menu_text(
        update,
        context
    )