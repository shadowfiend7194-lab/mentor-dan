from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from database.habits import (
    get_habit,
    mark_habit_reviewed,
    mark_habit_formed,
    mark_habit_controlled,
)

from database.events import add_event

from database.achievements import (
    check_and_award_achievements,
)

# =========================================================
# ПРОВЕРКА ХОРОШЕЙ ПРИВЫЧКИ
# =========================================================

async def habit_review_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data


    # =====================================================
    # ПАРСИНГ ID
    # =====================================================

    try:

        habit_id = int(
            data.rsplit(
                "_",
                1
            )[1]
        )

    except (
        ValueError,
        IndexError
    ):

        return


    user_id = update.effective_user.id


    habit = get_habit(
        user_id,
        habit_id
    )


    if not habit:
        return


    # =====================================================
    # ПРИВЫЧКА СФОРМИРОВАНА
    # =====================================================

    if data.startswith(
        "habit_review_formed_"
    ):

        mark_habit_formed(
            user_id,
            habit_id
        )
        
        mark_habit_reviewed(
            user_id,
            habit_id,
            datetime.now().strftime("%Y-%m-%d")
        )

        add_event(
            user_id=user_id,
            event_type=f"habit_formed_{habit_id}",
            title="Привычка закреплена",
            description=(
                f"Привычка «{habit['name']}» стала частью твоего ритма.\n\n"
                "Ты не просто попробовал — ты доказал себе, "
                "что можешь быть стабильным и доводить изменения до результата.\n\n"
                "Именно из таких маленьких побед постепенно строится новая версия тебя "
            )
        )

        await check_and_award_achievements(
            update,
            context
        )

        await query.message.reply_text(
            "🌳 Отлично.\n\n"
            f"Ты сформировал привычку «{habit['name']}».\n\n"
            "Когда-то это требовало усилий, а теперь стало частью твоего образа жизни.\n\n"
            "Запомни этот момент: ты доказал себе, что способен менять себя через маленькие ежедневные действия.\n\n"
            "Продолжай. Следующая маленькая победа уже ближе 💪"
        )


        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return

    # =====================================================
    # ПЛОХАЯ ПРИВЫЧКА ПОД КОНТРОЛЕМ
    # =====================================================

    if data.startswith(
        "bad_habit_controlled_"
    ):

        mark_habit_controlled(
            user_id,
            habit_id
        )


        mark_habit_reviewed(
            user_id,
            habit_id,
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )


        add_event(
            user_id=user_id,
            event_type=f"bad_habit_controlled_{habit_id}",
            title="Привычка осталась в прошлом",
            description=(
                f"Ты подтвердил, что смог оставить привычку "
                f"«{habit['name']}» в прошлом.\n\n"
                "Это уже не просто попытка на несколько дней — "
                "ты изменил своё поведение и сделал выбор в пользу себя."
            )
        )

        await check_and_award_achievements(
            update,
            context
        )

        await query.message.reply_text(
            "🛡️ Отлично.\n\n"
            f"Похоже, привычка «{habit['name']}» "
            "действительно осталась в прошлом.\n\n"
            "Ты не просто продержался несколько дней — "
            "ты смог изменить своё поведение и отказаться "
            "от того, что больше не хочешь видеть в своей жизни.\n\n"
            "Теперь главное — сохранить этот результат 💪"
        )

        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return


    # =====================================================
    # ПЛОХАЯ ПРИВЫЧКА — ПОКА ПРОДОЛЖАЮ
    # =====================================================

    if data.startswith(
        "bad_habit_continue_"
    ):

        mark_habit_reviewed(
            user_id,
            habit_id,
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )

        await query.message.reply_text(
            "💪 Хорошо.\n\n"
            f"«{habit['name']}»\n\n"
            "Продолжаем. Главное — ты не бросаешь работу над собой.\n\n"
            "Я спрошу тебя снова позже."
        )

        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return
    # =====================================================
    # ПОКА НЕ СФОРМИРОВАНА
    # =====================================================

    if data.startswith(
        "habit_review_continue_"
    ):

        mark_habit_reviewed(
            user_id,
            habit_id,
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )


        await query.message.reply_text(
            "💪 Пока продолжаем.\n\n"
            f"«{habit['name']}»\n\n"
            "Ничего не сбрасываем. "
            "Я спрошу тебя снова позже."
        )


        from handlers.menu import show_menu

        await show_menu(
            update,
            context
        )

        return