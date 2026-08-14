from telegram import Update
from telegram.ext import ContextTypes

from handlers.day.habits import habit_callback
from handlers.day.morning import morning_checkin
from handlers.day.evening import start_evening_checkin

from handlers.day.evening import handle_evening_text

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

        await query.answer()

        await morning_checkin(
            update,
            context
        )

        return

    # =====================================================
    # ВЕЧЕР
    # =====================================================

    if data == "day_evening":

        await query.answer()

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
    # ПУСТЫЕ КНОПКИ
    # =====================================================

    if data == "day_no_action":

        await query.answer()

        return