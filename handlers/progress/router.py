from telegram import Update
from telegram.ext import ContextTypes

from handlers.progress.screen import show_progress

from handlers.progress.history import show_history

from handlers.progress.achievements import (
    show_achievements,
)

# =========================================================
# CALLBACK РОУТЕР ПРОГРЕССА
# =========================================================

async def progress_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    data = query.data


    # =====================================================
    # НАЗАД / ОБНОВИТЬ ПРОГРЕСС
    # =====================================================

    if data == "open_progress":

        await query.answer()

        await show_progress(
            update,
            context
        )

        return


    # =====================================================
    # ДОСТИЖЕНИЯ
    # =====================================================

    if data == "progress_achievements":

        await show_achievements(
            update,
            context
        )

        return


    # =====================================================
    # ИСТОРИЯ ПУТИ
    # =====================================================

    if data == "progress_history":

        await show_history(
            update,
            context
        )

        return

    # =====================================================
    # НЕДЕЛЬНЫЙ АНАЛИЗ
    # =====================================================

    if data == "progress_weekly":

        await query.answer()

        await query.message.reply_text(
            "🧠 <b>Недельный анализ</b>\n\n"
            "Здесь появится глубокий анализ недели:\n\n"
            "📊 Результаты недели\n"
            "🕸 Радар состояния\n"
            "🤖 Анализ Дэна\n"
            "🎯 Фокус недели",
            parse_mode="HTML"
        )

        return
    
    # =====================================================
    # НАЗАД В ПРОГРЕСС
    # =====================================================

    if data == "back_to_progress":

        await query.answer()

        await show_progress(
            update,
            context
        )

        return