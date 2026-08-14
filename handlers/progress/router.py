from telegram import Update
from telegram.ext import ContextTypes

from handlers.progress.screen import show_progress


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

        await query.answer()

        await query.message.reply_text(
            "🏆 <b>Достижения</b>\n\n"
            "🔒 Знакомство с Дэном\n"
            "Пройди первый этап вместе с наставником.\n\n"

            "🔒 7 дней вместе с Дэном\n"
            "Продолжай работать над собой неделю подряд.\n\n"

            "🔒 Первая серия\n"
            "Создай свою первую стабильную серию выполнения.\n",
            parse_mode="HTML"
        )

        return


    # =====================================================
    # ИСТОРИЯ ПУТИ
    # =====================================================

    if data == "progress_history":

        await query.answer()

        await query.message.reply_text(
            "🛤️ <b>История пути</b>\n\n"
            "Здесь будет твоя история развития:\n\n"
            "• первый день с Дэном\n"
            "• полученные достижения\n"
            "• важные изменения\n"
            "• личные победы",
            parse_mode="HTML"
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
    
    if data == "back_to_progress":

        from handlers.progress.screen import show_progress

        await show_progress(
            update,
            context
        )

        return