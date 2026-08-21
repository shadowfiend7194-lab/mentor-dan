from telegram import Update
from telegram.ext import ContextTypes

from handlers.progress.weekly_report import (
    generate_weekly_report,
)

from database.weekly_reports import (
    save_weekly_report,
)


# =========================================================
# ТЕСТ НЕДЕЛЬНОГО ОТЧЁТА
# =========================================================

async def test_weekly_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    
    user_id = update.effective_user.id


    text = generate_weekly_report(
        user_id
    )


    save_weekly_report(
        user_id,
        text
    )


    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )