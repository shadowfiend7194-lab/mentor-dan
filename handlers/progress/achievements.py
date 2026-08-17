from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from database.achievements import (
    get_achievements_status,
)


async def show_achievements(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user_id = update.effective_user.id

    achievements = get_achievements_status(
        user_id
    )

    earned_count = sum(
        1
        for item in achievements
        if item["earned"]
    )

    text = (
        "🏆 <b>Достижения</b>\n\n"
        f"Получено: <b>{earned_count} / "
        f"{len(achievements)}</b>\n\n"
    )

    current_category = None

    for achievement in achievements:

        category = achievement["category"]

        if category != current_category:

            text += (
                f"\n<b>{category}</b>\n\n"
            )

            current_category = category

        # =================================================
        # ПОЛУЧЕНОЕ ДОСТИЖЕНИЕ
        # =================================================

        if achievement["earned"]:

            text += (
                f"{achievement['emoji']} "
                f"<b>{achievement['title']}</b>\n"
                f"{achievement['condition']}\n"
                f"<i>{achievement['description']}</i>\n\n"
            )

        # =================================================
        # ЗАКРЫТОЕ ДОСТИЖЕНИЕ
        # =================================================

        else:

            text += (
                f"🔒 <b>{achievement['title']}</b>\n"
                f"{achievement['condition']}\n\n"
            )

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="back_to_progress"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )