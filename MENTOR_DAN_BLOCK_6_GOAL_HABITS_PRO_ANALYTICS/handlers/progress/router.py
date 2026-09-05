from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.progress.screen import show_progress
from handlers.progress.history import show_history
from handlers.progress.achievements import show_achievements

from database.weekly_reports import get_last_reports


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

        await show_achievements(
            update,
            context
        )

        return


    # =====================================================
    # ИСТОРИЯ ПУТИ
    # =====================================================

    if data == "progress_history":

        await query.answer()

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
        user_id = update.effective_user.id

        from services.subscription import user_has_pro
        if user_has_pro(user_id):
            from services.dan.pro_weekly_report import build_weekly_report
            from database.weekly_reports import save_weekly_report

            text, chart = build_weekly_report(user_id)
            if text:
                save_weekly_report(user_id, text)
            if chart:
                await query.message.reply_photo(photo=chart)
            await query.message.reply_text(
                text or "Пока недостаточно данных для отчёта.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_progress")]
                ])
            )
            return

        reports = get_last_reports(user_id, limit=1)
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_progress")]]
        if not reports:
            text = (
                "🧠 <b>Недельный анализ</b>\n\n"
                "Пока здесь ещё нет готового отчёта.\n\n"
                "Дэн подготовит первый недельный анализ после завершения твоей первой недели наблюдений."
            )
        else:
            _, text = reports[0]

        await query.message.edit_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
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