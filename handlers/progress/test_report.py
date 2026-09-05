from telegram import Update
from telegram.ext import ContextTypes

from services.subscription import user_has_pro
from services.dan.pro_weekly_report import build_weekly_report
from database.weekly_reports import save_weekly_report


async def _send_report(update, user_id, current=False):
    text, chart = build_weekly_report(
        user_id,
        week_mode="current" if current else "previous",
    )

    # Превью текущей недели не записываем в историю:
    # это тестовый срез, а не завершённый недельный отчёт.
    if text and not current:
        save_weekly_report(
            user_id,
            text
        )

    if chart:
        await update.message.reply_photo(
            photo=chart
        )

    await update.message.reply_text(
        text or "Недостаточно данных.",
        parse_mode="HTML",
    )


async def test_weekly_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    if not user_has_pro(user_id):
        await update.message.reply_text(
            "⭐ Тест расширенного отчёта доступен только в PRO."
        )
        return

    await _send_report(
        update,
        user_id,
        current=False
    )


async def test_weekly_report_current(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    if not user_has_pro(user_id):
        await update.message.reply_text(
            "⭐ Тест расширенного отчёта доступен только в PRO."
        )
        return

    await _send_report(
        update,
        user_id,
        current=True
    )