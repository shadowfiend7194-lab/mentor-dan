import logging

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN

from database.init import init_db
from database.migrations import migrate

from handlers.start import start

from handlers.onboarding.router import (
    text_router,
    onboarding_callback_router,
)

from handlers.day.router import day_callback_router
from handlers.day.screen import show_day

from handlers.goal.router import goal_callback_router

from handlers.progress.router import progress_callback_router

from handlers.settings import (
    show_sleep_settings,
    change_wake_time,
    change_sleep_time,
    show_notification_settings,
    toggle_morning_notifications,
    toggle_evening_notifications,
    start_feedback,
    cancel_feedback,
    show_dan_memory,
    confirm_delete_user_data,
    cancel_delete_user_data,
    confirm_delete_all_user_data,
)

from handlers.dan.router import (
    dan_text_router,
    open_dan,
)

from handlers.menu import (
    menu_text,
    show_menu,
    show_settings,
)

from handlers.pro import (
    show_pro,
    show_pro_features,
    subscribe_pro,
    test_activate_pro,
    back_to_pro,
)

from scheduler.notifications import check_notifications

from handlers.day.notifications import delay_morning_checkin
from handlers.day.notifications import delay_evening_checkin

from utils.error_handler import (
    error_handler,
    get_friendly_error,
)

from handlers.habit_review import (
    habit_review_callback,
)

from handlers.progress.test_report import test_weekly_report

from handlers.feedback import (
    handle_feedback_message,
)

from handlers.goal.add_habit import (
    save_new_habit_name,
    save_custom_habit_days,
    save_habit_motivation,
)

from handlers.goal.edit_goal import (
    goal_text_router,
)

from database.connection import get_connection


from handlers.pro_setup import (
    pro_setup_add_goal,
    save_pro_setup_goal,
    pro_setup_goals_done,

    pro_setup_habit_start,
    pro_setup_difficulty,
    pro_setup_motivation,

    pro_setup_goal_new,
    save_goal_from_habit,
    pro_setup_goal_selected,

    pro_setup_add_habit,
    pro_setup_new_habit_type,
    save_new_pro_habit_name,
    pro_setup_new_frequency,
    save_new_pro_habit_days,
    pro_setup_new_difficulty,
    save_new_pro_habit_motivation,

    pro_setup_new_goal_create,
    save_new_habit_goal_name,
    pro_setup_new_goal_selected,

    pro_setup_finish,
    pro_setup_later,

    pro_setup_text_router,
)

# =========================================================
# ЛОГИРОВАНИЕ
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# ТЕКСТОВОЙ РОУТЕР СОЗДАНИЯ ПРИВЫЧКИ
# =========================================================

async def habit_creation_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = context.user_data.get(
        "add_habit_state"
    )

    # -----------------------------------------------------
    # НАЗВАНИЕ ПРИВЫЧКИ
    # -----------------------------------------------------

    if state == "name":

        await save_new_habit_name(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # СВОИ ДНИ
    # -----------------------------------------------------

    if state == "frequency_custom":

        await save_custom_habit_days(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # МОТИВАЦИЯ
    # -----------------------------------------------------

    if state == "motivation":

        await save_habit_motivation(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ СОЗДАЁТ ПРИВЫЧКУ
    # -----------------------------------------------------

    await text_router(
        update,
        context
    )


# =========================================================
# ЗАПУСК БОТА
# =========================================================

def main():

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    init_db()
    migrate()


    # -----------------------------------------------------
    # TELEGRAM APPLICATION
    # -----------------------------------------------------

    app = (
        Application.builder()
        .token(BOT_TOKEN)

        .connection_pool_size(50)
        .pool_timeout(30)

        .get_updates_connection_pool_size(10)
        .get_updates_pool_timeout(30)

        .connect_timeout(30)
        .get_updates_connect_timeout(30)

        .read_timeout(60)
        .get_updates_read_timeout(60)

        .write_timeout(60)
        .get_updates_write_timeout(60)

        .get_updates_http_version("1.1")

        .build()
    )


    # -----------------------------------------------------
    # ОБРАБОТКА ОШИБОК
    # -----------------------------------------------------

    app.add_error_handler(
        error_handler
    )


    # =====================================================
    # УВЕДОМЛЕНИЯ ДЭНА
    # =====================================================

    app.job_queue.run_repeating(
        check_notifications,
        interval=60,
        first=10
    )


    # =====================================================
    # /RESET_TEST
    # =====================================================

    async def reset_test(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        context.user_data.clear()

        context.user_data[
            "reset_onboarding_test"
        ] = True

        await update.message.reply_text(
            "🔄 Тестовый режим включён.\n\n"
            "Теперь отправь /start — онбординг "
            "запустится заново.\n\n"
            "Данные пользователя, цели, привычки "
            "и память Дэна не удаляются."
        )

        # =====================================================
    # /DEBUG_HABITS
    # =====================================================

    async def debug_habits(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user_id = update.effective_user.id

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                habit_type,
                frequency,
                schedule_days,
                active
            FROM habits
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,)
        )

        habits = cursor.fetchall()

        conn.close()

        if not habits:

            await update.message.reply_text(
                "🔎 <b>Привычки не найдены.</b>\n\n"
                "В таблице habits для этого пользователя "
                "нет записей.",
                parse_mode="HTML"
            )

            return

        lines = [
            "🔎 <b>DEBUG — привычки в базе</b>\n"
        ]

        for habit in habits:

            habit_id = habit[0]
            name = habit[1]
            habit_type = habit[2]
            frequency = habit[3]
            schedule_days = habit[4]
            active = habit[5]

            icon = (
                "🟢"
                if habit_type == "good"
                else "🔴"
            )

            active_text = (
                "АКТИВНА"
                if active
                else "УДАЛЕНА"
            )

            lines.append(
                f"{icon} <b>ID {habit_id}</b>\n"
                f"Название: {name}\n"
                f"Тип: {habit_type}\n"
                f"Периодичность: {frequency}\n"
                f"Дни: {schedule_days or '—'}\n"
                f"Статус: <b>{active_text}</b>\n"
            )

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="HTML"
        )

    # =====================================================
    # /START
    # =====================================================

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    # =====================================================
    # /RESET_TEST
    # =====================================================

    app.add_handler(
        CommandHandler(
            "reset_test",
            reset_test
        )
    )

    # =====================================================
    # /DEBUG_HABITS
    # =====================================================

    app.add_handler(
        CommandHandler(
            "debug_habits",
            debug_habits
        )
    )


    # =====================================================
    # DAY CALLBACKS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            day_callback_router,
            pattern=(
                r"^(day_habit_\d+|day_morning|"
                r"day_evening|go_menu|day_no_action)$"
            )
        )
    )


    # =====================================================
    # GOAL CALLBACKS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            goal_callback_router,
            pattern=(
                r"^(goal_review_achieved|"
                r"goal_review_continue|"
                r"goal_review_back)$"
            )
        )
    )


    # =====================================================
    # GOAL / HABITS CALLBACKS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            goal_callback_router,
            pattern=(
                r"^(goal_back|"
                r"goal_edit|"
                r"goal_manage_\d+|"
                r"goal_rename_\d+|"
                r"goal_add_pro|"
                r"goal_delete_\d+|"
                r"goal_delete_confirm_\d+|"
                r"goal_habits|"
                r"goal_delete_\d+|"
                r"goal_delete_confirm_\d+|"
                r"habit_pro_locked_(difficulty|motivation|goal)_\d+|"
                r"habit_pro_difficulty_\d+|"
                r"habit_pro_motivation_\d+|"
                r"habit_pro_goal_\d+|"
                r"habit_pro_set_difficulty_\d+_[1-5]|"
                r"habit_pro_set_goal_\d+_(none|\d+)|"
                r"habit_difficulty_\d+|"
                r"set_habit_difficulty_[1-5]|"
                r"habit_goal_\d+|"
                r"set_habit_goal_(none|\d+)|"
                r"habit_motivation_\d+|"
                r"habit_edit|"
                r"habit_edit_good|"
                r"habit_edit_bad|"
                r"habit_delete|"
                r"habit_delete_\d+|"
                r"habit_delete_confirm_\d+|"
                r"habit_add_pro|"
                r"add_habit_good|"
                r"add_habit_bad|"
                r"add_habit_frequency_daily|"
                r"add_habit_frequency_weekdays|"
                r"add_habit_frequency_custom|"
                r"add_habit_difficulty_[1-5]|"
                r"add_habit_goal_(none|\d+)|"
                r"habit_edit_\d+|"
                r"habit_name_\d+|"
                r"habit_frequency_\d+|"
                r"edit_frequency_daily|"
                r"edit_frequency_weekdays|"
                r"edit_frequency_custom)$"
            )
        )
    )


    # =====================================================
    # HABIT REVIEWS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            habit_review_callback,
            pattern=(
                r"^(habit_review_(formed|continue)_\d+|"
                r"bad_habit_(controlled|continue)_\d+)$"
            )
        )
    )


    # =====================================================
    # PROGRESS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            progress_callback_router,
            pattern=(
                r"^(open_progress|"
                r"progress_achievements|"
                r"progress_history|"
                r"progress_weekly|"
                r"back_to_progress|"
                r"go_menu)$"
            )
        )
    )


    # =====================================================
    # ONBOARDING CALLBACKS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            onboarding_callback_router,
            pattern=(
                r"^(start_intro|"
                r"why_intro|"
                r"back_to_start|"
                r"age_under_18|"
                r"age_18_25|"
                r"age_26_35|"
                r"age_35_plus|"
                r"good_frequency_daily|"
                r"good_frequency_weekdays|"
                r"good_frequency_custom|"
                r"bad_habit_yes|"
                r"bad_habit_no|"
                r"bad_frequency_daily|"
                r"bad_frequency_weekdays|"
                r"bad_frequency_custom|"
                r"oath_accept|"
                r"open_main_menu)$"
            )
        )
    )


    # =====================================================
    # SETTINGS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            show_sleep_settings,
            pattern="^settings_sleep$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            change_wake_time,
            pattern="^change_wake_time$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            change_sleep_time,
            pattern="^change_sleep_time$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            show_settings,
            pattern="^back_to_settings$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            show_notification_settings,
            pattern="^settings_notifications$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            toggle_morning_notifications,
            pattern="^toggle_morning_notifications$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            toggle_evening_notifications,
            pattern="^toggle_evening_notifications$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            start_feedback,
            pattern=r"^(suggest_feature|report_problem)$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            cancel_feedback,
            pattern="^feedback_cancel$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            show_dan_memory,
            pattern="^settings_memory$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            confirm_delete_user_data,
            pattern="^delete_my_data$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            cancel_delete_user_data,
            pattern="^cancel_delete_data$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            confirm_delete_all_user_data,
            pattern="^confirm_delete_all$"
        )
    )

    


    # =====================================================
    # PRO SETUP
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_add_goal,
            pattern=r"^pro_setup_add_goal$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_goals_done,
            pattern=r"^pro_setup_goals_done$"
        )
    )

    # -----------------------------------------------------
    # СУЩЕСТВУЮЩИЕ ПРИВЫЧКИ
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_habit_start,
            pattern=r"^pro_setup_habit_start$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_difficulty,
            pattern=r"^pro_setup_difficulty_[1-5]$"
        )
    )

    # -----------------------------------------------------
    # ЦЕЛИ СУЩЕСТВУЮЩИХ ПРИВЫЧЕК
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_goal_new,
            pattern=r"^pro_setup_goal_new$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_goal_selected,
            pattern=r"^pro_setup_goal_(none|\d+)$"
        )
    )

    # -----------------------------------------------------
    # НОВАЯ ПРИВЫЧКА
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_add_habit,
            pattern=r"^pro_setup_add_habit$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_new_habit_type,
            pattern=r"^pro_setup_new_(good|bad)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_new_frequency,
            pattern=(
                r"^pro_setup_new_frequency_"
                r"(daily|weekdays|custom)$"
            )
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_new_difficulty,
            pattern=r"^pro_setup_new_difficulty_[1-5]$"
        )
    )

    # -----------------------------------------------------
    # ЦЕЛЬ НОВОЙ ПРИВЫЧКИ
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_new_goal_create,
            pattern=r"^pro_setup_new_goal_create$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_new_goal_selected,
            pattern=r"^pro_setup_new_goal_(none|\d+)$"
        )
    )

    # -----------------------------------------------------
    # ЗАВЕРШЕНИЕ
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_finish,
            pattern=r"^pro_setup_finish$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            pro_setup_later,
            pattern=r"^pro_setup_later$"
        )
    )
    

    # =====================================================
    # ПРИОРИТЕТНЫЙ ТЕКСТОВЫЙ РОУТЕР
    # =====================================================
    # В PTB внутри одной группы обрабатывается только первый подходящий
    # MessageHandler. Поэтому goal_text_router и pro_setup_text_router
    # нельзя держать двумя отдельными обработчиками в одной группе:
    # второй никогда не получит сообщение.

    async def priority_text_router(update, context):
        handled = await goal_text_router(update, context)
        if handled:
            return

        handled = await pro_setup_text_router(update, context)
        if handled:
            return

        # Ничего не перехватываем: обработку продолжит group=0.
        return

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            priority_text_router
        ),
        group=-1
    )


    # =====================================================
    # PRO
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            show_pro,
            pattern=r"^pro_back$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            show_pro_features,
            pattern=r"^pro_features$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            subscribe_pro,
            pattern=r"^pro_subscribe$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            test_activate_pro,
            pattern=r"^pro_test_activate$"
        )
    )


    # =====================================================
    # DELAY NOTIFICATIONS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            delay_morning_checkin,
            pattern="^delay_morning_checkin$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            delay_evening_checkin,
            pattern="^delay_evening_checkin$"
        )
    )


    # =====================================================
    # WEEKLY REPORT TEST
    # =====================================================

    app.add_handler(
        CommandHandler(
            "reporttest",
            test_weekly_report
        )
    )


    # =====================================================
    # DAY
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            show_day,
            pattern="^open_day$"
        )
    )


    # =====================================================
    # ОБРАТНАЯ СВЯЗЬ
    # =====================================================

    app.add_handler(
        MessageHandler(
            (
                (filters.TEXT & ~filters.COMMAND)
                | filters.PHOTO
            ),
            handle_feedback_message
        ),
        group=1
    )


    # =====================================================
    # ТЕКСТОВЫЕ КНОПКИ ГЛАВНОГО МЕНЮ
    # =====================================================

    app.add_handler(
        MessageHandler(
            filters.Regex(
                r"^(📅 Мой день|"
                r"🎯 Моя цель|"
                r"📊 Мой прогресс|"
                r"💬 Дэн|"
                r"⚙️ Настройки|"
                r"⭐ PRO)$"
            ),
            menu_text
        )
    )


    # =====================================================
    # СОЗДАНИЕ ПРИВЫЧКИ — ТЕКСТОВЫЕ ШАГИ
    # =====================================================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            habit_creation_text_router
        )
    )


    # =====================================================
    # ЗАПУСК
    # =====================================================

    logger.info(
        "🚀 Дэн v2 запускается"
    )

    print(
        "🚀 Дэн v2 запущен"
    )


    try:

        app.run_polling(
            drop_pending_updates=True
        )

    except Exception as error:

        logger.exception(
            "КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ ДЭНА"
        )

        print()
        print(
            get_friendly_error(error)
        )
        print()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

