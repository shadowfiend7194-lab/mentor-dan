from datetime import date, timedelta

from database.connection import get_connection
from database.habits import (
    get_user_habits,
    is_habit_scheduled_on_date,
)


# =========================================================
# ЛОГИ ПРИВЫЧЕК
# =========================================================

def get_habit_logs(
    habit_id,
    start_date,
    end_date,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            date,
            completed
        FROM habit_logs
        WHERE habit_id = ?
        AND date >= ?
        AND date <= ?
        """,
        (
            habit_id,
            start_date.isoformat(),
            end_date.isoformat(),
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        row[0]: bool(row[1])
        for row in rows
    }


# =========================================================
# ТЕКУЩАЯ СЕРИЯ
# =========================================================
#
# ВАЖНО:
# Если сегодня ещё ничего не отмечено,
# сегодняшний день НЕ ломает вчерашнюю серию.
#
# Например:
#
# 20 — выполнено
# 21 — выполнено
# 22 — выполнено
# 23 — выполнено
# 24 — сегодня, ещё не отмечено
#
# current_streak = 4
#
# =========================================================

def get_current_streak(
    habit,
    logs,
    today,
):

    streak = 0

    current = today

    # -----------------------------------------------------
    # Если сегодня привычка запланирована, но ещё
    # не выполнена — начинаем проверку со вчера.
    # -----------------------------------------------------

    today_key = today.isoformat()

    if (
        is_habit_scheduled_on_date(
            habit,
            today,
        )
        and not logs.get(
            today_key,
            False,
        )
    ):

        current -= timedelta(days=1)

    # -----------------------------------------------------
    # Ищем непрерывную серию назад
    # -----------------------------------------------------

    for _ in range(365):

        if not is_habit_scheduled_on_date(
            habit,
            current,
        ):

            current -= timedelta(days=1)

            continue

        if logs.get(
            current.isoformat(),
            False,
        ):

            streak += 1

            current -= timedelta(days=1)

            continue

        break

    return streak


# =========================================================
# ЛУЧШАЯ СЕРИЯ
# =========================================================

def get_best_streak(
    habit,
    logs,
    start_date,
    end_date,
):

    best = 0
    current_streak = 0

    current = start_date

    while current <= end_date:

        if is_habit_scheduled_on_date(
            habit,
            current,
        ):

            if logs.get(
                current.isoformat(),
                False,
            ):

                current_streak += 1

                best = max(
                    best,
                    current_streak,
                )

            else:

                current_streak = 0

        current += timedelta(days=1)

    return best


# =========================================================
# СТАТИСТИКА ПЕРИОДА
# =========================================================

def get_period_stats(
    habit,
    logs,
    start_date,
    end_date,
    today,
):

    scheduled = 0
    completed = 0
    pending = 0
    missed = 0

    current = start_date

    while current <= end_date:

        if is_habit_scheduled_on_date(
            habit,
            current,
        ):

            scheduled += 1

            is_completed = logs.get(
                current.isoformat(),
                False,
            )

            # -------------------------------------------------
            # Выполнено
            # -------------------------------------------------

            if is_completed:

                completed += 1

            # -------------------------------------------------
            # Прошедший день и не выполнено
            # -------------------------------------------------

            elif current < today:

                missed += 1

            # -------------------------------------------------
            # Сегодня
            # -------------------------------------------------

            elif current == today:

                pending += 1

            # -------------------------------------------------
            # Будущий день
            # -------------------------------------------------

            else:

                pending += 1

        current += timedelta(days=1)

    # ---------------------------------------------------------
    # Только реально прошедшие задания.
    #
    # Будущие и сегодняшние pending сюда НЕ входят.
    # ---------------------------------------------------------

    elapsed_scheduled = (
        completed
        + missed
    )

    # ---------------------------------------------------------
    # Если ещё ничего не прошло — статистики пока нет.
    # ---------------------------------------------------------

    if elapsed_scheduled:

        elapsed_rate = round(
            completed
            / elapsed_scheduled
            * 100,
            1,
        )

    else:

        elapsed_rate = None

    return {
        "scheduled": scheduled,

        "completed": completed,

        "missed": missed,

        "pending": pending,

        "elapsed_scheduled": (
            elapsed_scheduled
        ),

        "completion_rate": (
            elapsed_rate
        ),
    }


# =========================================================
# СТАТИСТИКА ОДНОЙ ПРИВЫЧКИ
# =========================================================

def get_habit_trend(
    habit,
    today,
):

    # -----------------------------------------------------
    # ПЕРИОДЫ
    # -----------------------------------------------------

    current_week_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    current_week_end = (
        current_week_start
        + timedelta(days=6)
    )

    previous_week_start = (
        current_week_start
        - timedelta(days=7)
    )

    previous_week_end = (
        current_week_start
        - timedelta(days=1)
    )

    period_start = previous_week_start

    period_end = current_week_end

    # -----------------------------------------------------
    # ЛОГИ
    # -----------------------------------------------------

    logs = get_habit_logs(
        habit["id"],
        period_start,
        period_end,
    )

    # -----------------------------------------------------
    # СТАТИСТИКА ТЕКУЩЕЙ НЕДЕЛИ
    # -----------------------------------------------------

    current_week = get_period_stats(
        habit,
        logs,
        current_week_start,
        current_week_end,
        today,
    )

    # -----------------------------------------------------
    # СТАТИСТИКА ПРОШЛОЙ НЕДЕЛИ
    # -----------------------------------------------------

    previous_week = get_period_stats(
        habit,
        logs,
        previous_week_start,
        previous_week_end,
        today,
    )

    # -----------------------------------------------------
    # ИЗМЕНЕНИЕ
    # -----------------------------------------------------
    #
    # Если текущая неделя ещё не имеет ни одного
    # завершённого/пропущенного задания,
    # сравнивать её с прошлой нельзя.
    #
    # Поэтому:
    #
    # change = None
    # trend = just_started
    #
    # Это КЛЮЧЕВОЕ изменение.
    # -----------------------------------------------------

    current_elapsed = (
        current_week[
            "elapsed_scheduled"
        ]
    )

    previous_elapsed = (
        previous_week[
            "elapsed_scheduled"
        ]
    )

    if current_elapsed == 0:

        change = None

        trend = "just_started"

    else:

        current_rate = (
            current_week[
                "completion_rate"
            ]
        )

        previous_rate = (
            previous_week[
                "completion_rate"
            ]
        )

        # Если прошлой недели ещё не было данных,
        # сравнение тоже бессмысленно.
        if previous_rate is None:

            change = None

            trend = "not_enough_data"

        else:

            change = round(
                current_rate
                - previous_rate,
                1,
            )

            if change >= 15:

                trend = (
                    "strong_improvement"
                )

            elif change >= 5:

                trend = "improvement"

            elif change <= -15:

                trend = "strong_decline"

            elif change <= -5:

                trend = "decline"

            else:

                trend = "stable"

    # -----------------------------------------------------
    # СЕГОДНЯ
    # -----------------------------------------------------

    today_stats = get_period_stats(
        habit,
        logs,
        today,
        today,
        today,
    )

    # -----------------------------------------------------
    # ПОСЛЕДНИЕ 7 ДНЕЙ
    # -----------------------------------------------------

    recent_days = []

    recent_start = (
        today
        - timedelta(days=6)
    )

    current = recent_start

    while current <= today:

        scheduled = is_habit_scheduled_on_date(
            habit,
            current,
        )

        completed = logs.get(
            current.isoformat(),
            False,
        )

        if scheduled:

            if completed:

                status = "completed"

            elif current < today:

                status = "missed"

            else:

                status = "pending"

        else:

            status = "not_scheduled"

        recent_days.append(
            {
                "date": current.isoformat(),

                "scheduled": scheduled,

                "completed": completed,

                "status": status,
            }
        )

        current += timedelta(days=1)

    # -----------------------------------------------------
    # ПОСЛЕДНЕЕ ВЫПОЛНЕНИЕ
    # -----------------------------------------------------

    completed_dates = [
        key
        for key, value in logs.items()
        if value
    ]

    last_completed_date = (
        max(completed_dates)
        if completed_dates
        else None
    )

    # -----------------------------------------------------
    # СЕРИИ
    # -----------------------------------------------------

    current_streak = get_current_streak(
        habit,
        logs,
        today,
    )

    best_streak = get_best_streak(
        habit,
        logs,
        period_start,
        period_end,
    )

    # -----------------------------------------------------
    # РЕЗУЛЬТАТ
    # -----------------------------------------------------

    return {
        "id": habit["id"],

        "name": habit["name"],

        "type": habit["habit_type"],

        "frequency": habit["frequency"],

        "formed": habit.get(
            "formed",
            False,
        ),

        "controlled": habit.get(
            "controlled",
            False,
        ),

        # -------------------------------------------------
        # ТЕКУЩАЯ НЕДЕЛЯ
        # -------------------------------------------------

        "current_week": {
            "scheduled": (
                current_week[
                    "scheduled"
                ]
            ),

            "completed": (
                current_week[
                    "completed"
                ]
            ),

            "missed": (
                current_week[
                    "missed"
                ]
            ),

            "pending": (
                current_week[
                    "pending"
                ]
            ),

            "elapsed_scheduled": (
                current_week[
                    "elapsed_scheduled"
                ]
            ),

            "completion_rate": (
                current_week[
                    "completion_rate"
                ]
            ),
        },

        # -------------------------------------------------
        # ПРОШЛАЯ НЕДЕЛЯ
        # -------------------------------------------------

        "previous_week": {
            "scheduled": (
                previous_week[
                    "scheduled"
                ]
            ),

            "completed": (
                previous_week[
                    "completed"
                ]
            ),

            "missed": (
                previous_week[
                    "missed"
                ]
            ),

            "pending": (
                previous_week[
                    "pending"
                ]
            ),

            "elapsed_scheduled": (
                previous_week[
                    "elapsed_scheduled"
                ]
            ),

            "completion_rate": (
                previous_week[
                    "completion_rate"
                ]
            ),
        },

        # -------------------------------------------------
        # СЕГОДНЯ
        # -------------------------------------------------

        "today": {
            "scheduled": (
                today_stats[
                    "scheduled"
                ]
            ),

            "completed": (
                today_stats[
                    "completed"
                ]
            ),

            "missed": (
                today_stats[
                    "missed"
                ]
            ),

            "pending": (
                today_stats[
                    "pending"
                ]
            ),

            "completion_rate": (
                today_stats[
                    "completion_rate"
                ]
            ),
        },

        # -------------------------------------------------
        # ТРЕНД
        # -------------------------------------------------

        "change_percentage_points": (
            change
        ),

        "trend": trend,

        # -------------------------------------------------
        # СЕРИИ
        # -------------------------------------------------

        "current_streak": (
            current_streak
        ),

        "best_streak_14_days": (
            best_streak
        ),

        # -------------------------------------------------
        # ПОСЛЕДНЕЕ ВЫПОЛНЕНИЕ
        # -------------------------------------------------

        "last_completed_date": (
            last_completed_date
        ),

        # -------------------------------------------------
        # ПОСЛЕДНИЕ ДНИ
        # -------------------------------------------------

        "recent_days": recent_days,
    }


# =========================================================
# УДАЛЁННЫЕ ПРИВЫЧКИ
# =========================================================
#
# В текущей БД нет removed_at.
#
# Поэтому используем:
#
# active = 0
#
# Это позволяет Дэну видеть старые привычки,
# которые пользователь когда-то удалил.
#
# В дальнейшем сюда можно добавить:
# - deleted_at
# - delete_reason
# - replacement_habit_id
#
# для Pro-аналитики.
# =========================================================

def get_removed_habits_history(
    user_id,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            habit_type,
            frequency,
            created_at
        FROM habits
        WHERE user_id = ?
        AND active = 0
        ORDER BY id DESC
        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],

            "name": row[1],

            "type": row[2],

            "frequency": row[3],

            "created_at": row[4],
        }
        for row in rows
    ]


# =========================================================
# ОБЩАЯ АНАЛИТИКА ПРИВЫЧЕК
# =========================================================

def get_habit_trends(
    user_id,
):

    habits = get_user_habits(
        user_id
    )

    today = date.today()

    result = []

    for habit in habits:

        result.append(
            get_habit_trend(
                habit,
                today,
            )
        )

    # -----------------------------------------------------
    # ОБЩАЯ СТАТИСТИКА
    # -----------------------------------------------------

    current_scheduled = 0
    current_completed = 0
    current_missed = 0
    current_pending = 0

    previous_scheduled = 0
    previous_completed = 0
    previous_missed = 0
    previous_pending = 0

    for habit in result:

        current_scheduled += (
            habit[
                "current_week"
            ][
                "scheduled"
            ]
        )

        current_completed += (
            habit[
                "current_week"
            ][
                "completed"
            ]
        )

        current_missed += (
            habit[
                "current_week"
            ][
                "missed"
            ]
        )

        current_pending += (
            habit[
                "current_week"
            ][
                "pending"
            ]
        )

        previous_scheduled += (
            habit[
                "previous_week"
            ][
                "scheduled"
            ]
        )

        previous_completed += (
            habit[
                "previous_week"
            ][
                "completed"
            ]
        )

        previous_missed += (
            habit[
                "previous_week"
            ][
                "missed"
            ]
        )

        previous_pending += (
            habit[
                "previous_week"
            ][
                "pending"
            ]
        )

    # -----------------------------------------------------
    # ПРОШЕДШАЯ ЧАСТЬ ТЕКУЩЕЙ НЕДЕЛИ
    # -----------------------------------------------------

    current_elapsed = (
        current_completed
        + current_missed
    )

    previous_elapsed = (
        previous_completed
        + previous_missed
    )

    # -----------------------------------------------------
    # ТЕКУЩИЙ ПРОЦЕНТ
    # -----------------------------------------------------

    if current_elapsed:

        current_rate = round(
            current_completed
            / current_elapsed
            * 100,
            1,
        )

    else:

        current_rate = None

    # -----------------------------------------------------
    # ПРОШЛЫЙ ПРОЦЕНТ
    # -----------------------------------------------------

    if previous_elapsed:

        previous_rate = round(
            previous_completed
            / previous_elapsed
            * 100,
            1,
        )

    else:

        previous_rate = None

    # -----------------------------------------------------
    # ОБЩЕЕ ИЗМЕНЕНИЕ
    # -----------------------------------------------------
    #
    # КЛЮЧЕВО:
    #
    # если текущая неделя ещё не имеет
    # прошедших заданий — никакого decline.
    #
    # Дэн должен понимать:
    #
    # "Сегодня только понедельник,
    # ещё слишком рано оценивать неделю."
    #
    # -----------------------------------------------------

    if current_elapsed == 0:

        overall_change = None

        overall_trend = (
            "just_started"
        )

    elif previous_rate is None:

        overall_change = None

        overall_trend = (
            "not_enough_data"
        )

    else:

        overall_change = round(
            current_rate
            - previous_rate,
            1,
        )

        if overall_change >= 15:

            overall_trend = (
                "strong_improvement"
            )

        elif overall_change >= 5:

            overall_trend = (
                "improvement"
            )

        elif overall_change <= -15:

            overall_trend = (
                "strong_decline"
            )

        elif overall_change <= -5:

            overall_trend = (
                "decline"
            )

        else:

            overall_trend = "stable"

    # -----------------------------------------------------
    # СИЛЬНЕЙШИЕ УЛУЧШЕНИЯ
    # -----------------------------------------------------
    #
    # Если текущая неделя ещё не началась,
    # никаких "улучшений" тоже не показываем.
    #
    # -----------------------------------------------------

    if current_elapsed == 0:

        strongest_improvements = []

        strongest_declines = []

    else:

        strongest_improvements = sorted(
            [
                habit
                for habit in result
                if (
                    habit[
                        "change_percentage_points"
                    ] is not None
                    and
                    habit[
                        "change_percentage_points"
                    ] >= 5
                )
            ],
            key=lambda habit: (
                habit[
                    "change_percentage_points"
                ]
            ),
            reverse=True,
        )[:3]

        strongest_declines = sorted(
            [
                habit
                for habit in result
                if (
                    habit[
                        "change_percentage_points"
                    ] is not None
                    and
                    habit[
                        "change_percentage_points"
                    ] <= -5
                )
            ],
            key=lambda habit: (
                habit[
                    "change_percentage_points"
                ]
            ),
        )[:3]

    # -----------------------------------------------------
    # СЕГОДНЯ
    # -----------------------------------------------------

    today_stats = {
        "scheduled": sum(
            habit[
                "today"
            ][
                "scheduled"
            ]
            for habit in result
        ),

        "completed": sum(
            habit[
                "today"
            ][
                "completed"
            ]
            for habit in result
        ),

        "missed": sum(
            habit[
                "today"
            ][
                "missed"
            ]
            for habit in result
        ),

        "pending": sum(
            habit[
                "today"
            ][
                "pending"
            ]
            for habit in result
        ),
    }

    # -----------------------------------------------------
    # ИСТОРИЯ УДАЛЁННЫХ ПРИВЫЧЕК
    # -----------------------------------------------------

    removed_habits = (
        get_removed_habits_history(
            user_id
        )
    )

    # -----------------------------------------------------
    # РЕЗУЛЬТАТ
    # -----------------------------------------------------

    return {
        "period_days": 14,

        "overall": {
            "current_week": {
                "scheduled": (
                    current_scheduled
                ),

                "completed": (
                    current_completed
                ),

                "missed": (
                    current_missed
                ),

                "pending": (
                    current_pending
                ),

                "elapsed_scheduled": (
                    current_elapsed
                ),

                "completion_rate": (
                    current_rate
                ),
            },

            "previous_week": {
                "scheduled": (
                    previous_scheduled
                ),

                "completed": (
                    previous_completed
                ),

                "missed": (
                    previous_missed
                ),

                "pending": (
                    previous_pending
                ),

                "elapsed_scheduled": (
                    previous_elapsed
                ),

                "completion_rate": (
                    previous_rate
                ),
            },

            "change_percentage_points": (
                overall_change
            ),

            "trend": (
                overall_trend
            ),

            "missed_change": (
                (
                    current_missed
                    - previous_missed
                )
                if current_elapsed
                else None
            ),
        },

        # -------------------------------------------------
        # СЕГОДНЯ
        # -------------------------------------------------

        "today": today_stats,

        # -------------------------------------------------
        # СИЛЬНЕЙШИЕ ПАДЕНИЯ
        # -------------------------------------------------

        "strongest_declines": [
            {
                "name": habit["name"],

                "change_percentage_points": (
                    habit[
                        "change_percentage_points"
                    ]
                ),

                "current_rate": (
                    habit[
                        "current_week"
                    ][
                        "completion_rate"
                    ]
                ),

                "previous_rate": (
                    habit[
                        "previous_week"
                    ][
                        "completion_rate"
                    ]
                ),
            }

            for habit
            in strongest_declines
        ],

        # -------------------------------------------------
        # СИЛЬНЕЙШИЕ УЛУЧШЕНИЯ
        # -------------------------------------------------

        "strongest_improvements": [
            {
                "name": habit["name"],

                "change_percentage_points": (
                    habit[
                        "change_percentage_points"
                    ]
                ),

                "current_rate": (
                    habit[
                        "current_week"
                    ][
                        "completion_rate"
                    ]
                ),

                "previous_rate": (
                    habit[
                        "previous_week"
                    ][
                        "completion_rate"
                    ]
                ),
            }

            for habit
            in strongest_improvements
        ],

        # -------------------------------------------------
        # ВСЕ АКТИВНЫЕ ПРИВЫЧКИ
        # -------------------------------------------------

        "habits": result,

        # -------------------------------------------------
        # УДАЛЁННЫЕ ПРИВЫЧКИ
        # -------------------------------------------------

        "removed_habits": (
            removed_habits
        ),
    }