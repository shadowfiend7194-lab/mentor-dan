from telegram import Update
from telegram.ext import ContextTypes

from handlers.day.habits import habit_callback
from handlers.day.morning import morning_checkin
from handlers.day.evening import start_evening_checkin

from database.users import can_do_checkin

from handlers.day.notifications import (
    delay_morning_checkin,
    delay_evening_checkin,
)

async def day_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if not query:
        return

    data = query.data

    # =====================================================
    # ПРИВЫЧКА
    # =====================================================

    if data.startswith("day_habit_"):

        await habit_callback(
            update,
            context
        )

        return

    # =====================================================
    # УТРО
    # =====================================================

    if data == "day_morning":

        user_id = update.effective_user.id

        if not can_do_checkin(
            user_id,
            "morning"
        ):

            await query.answer(
                "☀️ Ты уже проходил утренний чек-ин сегодня",
                show_alert=True
            )
            return

        await morning_checkin(
            update,
            context
        )

        return

    # =====================================================
    # ВЕЧЕР
    # =====================================================

    if data == "day_evening":

        user_id = update.effective_user.id

        if not can_do_checkin(
            user_id,
            "evening"
        ):
            await query.answer(
                "🌙 Ты уже проходил вечерний чек-ин сегодня",
                show_alert=True
            )
            return

        await start_evening_checkin(
            update,
            context
        )

        return

    # =====================================================
    # ГЛАВНОЕ МЕНЮ
    # =====================================================

    if data == "go_menu":

        await query.answer()

        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return
    

    # =====================================================
    # ОТЛОЖИТЬ ЧЕК-ИН
    # =====================================================

    if data in {
        "morning_later",
        "evening_later",
    }:

        await query.answer()

        await query.edit_message_text(
            "👍 Хорошо.\n\n"
            "Вернёмся к этому позже."
        )

        return

    # =====================================================
    # ОТЛОЖИТЬ УТРО
    # =====================================================

    if data == "delay_morning_checkin":

        await delay_morning_checkin(
            update,
           context
        )

        return


    # =====================================================
    # ОТЛОЖИТЬ ВЕЧЕР
    # =====================================================

    if data == "delay_evening_checkin":

        await delay_evening_checkin(
            update,
            context
        )

        return
        
    # =====================================================
    # ПУСТЫЕ КНОПКИ
    # =====================================================

    if data == "day_no_action":

        await query.answer()

        return