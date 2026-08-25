import logging
import os

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

# =========================================================
# ЛОГИРОВАНИЕ
# =========================================================



logger = logging.getLogger(__name__)




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

    # =========================================================
    # /RESET_TEST — СБРОС ОНБОРДИНГА ДЛЯ ТЕСТИРОВАНИЯ
    # =========================================================

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
            pattern=r"goal_review_achieved|goal_review_continue|goal_review_back"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            goal_callback_router,
            pattern=(
                r"^(goal_back|goal_edit|goal_edit_current|goal_add_pro|"
                r"goal_habits|habit_edit|habit_edit_good|habit_edit_bad|"
                r"habit_add_pro|habit_edit_\d+|habit_name_\d+|"
                r"habit_frequency_\d+|"
                r"edit_frequency_daily|edit_frequency_weekdays|"
                r"edit_frequency_custom|"
                r"goal_review_achieved|goal_review_continue)$"
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
                r"^(open_progress|progress_achievements|"
                r"progress_history|progress_weekly|"
                r"back_to_progress|go_menu)$"
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
                r"^(start_intro|why_intro|back_to_start|"
                r"age_under_18|age_18_25|age_26_35|age_35_plus|"
                r"good_frequency_daily|good_frequency_weekdays|"
                r"good_frequency_custom|"
                r"bad_habit_yes|bad_habit_no|"
                r"bad_frequency_daily|bad_frequency_weekdays|"
                r"bad_frequency_custom|"
                r"oath_accept|open_main_menu)$"
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
                r"^(📅 Мой день|🎯 Моя цель|📊 Мой прогресс|💬 Дэн|⚙️ Настройки|⭐ PRO)$"
            ),
            menu_text
        )
    )

    # =====================================================
    # ОСТАЛЬНЫЕ ТЕКСТОВЫЕ СООБЩЕНИЯ
    # =====================================================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_router
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