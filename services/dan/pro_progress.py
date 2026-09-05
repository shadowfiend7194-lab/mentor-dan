from datetime import date, datetime, timedelta

from database.connection import get_connection
from services.subscription import is_pro


# =========================================================
# PROGRESS / PRO
# =========================================================
#
# ЕДИНАЯ МАТЕМАТИКА PRO
#
# привычка
#   ↓
# выполнение
#   ↓
# стабильность
#   ↓
# свежесть результата
#   ↓
# поправка на сложность
#   ↓
# прогресс формирования
#   ↓
# привычки → цель
#   ↓
# прогресс цели
#
# ВАЖНО:
#
# 1. Никаких новых таблиц для стабильности нет.
# 2. Никакие показатели не записываются в БД.
# 3. Всё считается на основе существующих habit_logs.
# 4. FREE этот файл вообще не использует.
#
# =========================================================


# =========================================================
# НАСТРОЙКИ МОДЕЛИ
# =========================================================

# ---------------------------------------------------------
# ОКНО СВЕЖЕСТИ
# ---------------------------------------------------------
#
# Последние 14 дней имеют больший вес.
#
# Это нужно, чтобы старые ошибки не тянулись
# за человеком бесконечно.
#
RECENT_WINDOW_DAYS = 14

# 70% — свежая динамика
# 30% — вся история
RECENT_STABILITY_WEIGHT = 0.70
ALL_TIME_STABILITY_WEIGHT = 0.30


# ---------------------------------------------------------
# ФОРМИРОВАНИЕ ПРИВЫЧКИ
# ---------------------------------------------------------

FORMATION_DAYS_BY_DIFFICULTY = {
    1: 21,
    2: 28,
    3: 35,
    4: 45,
    5: 60,
}


# ---------------------------------------------------------
# ТРЕБУЕМАЯ СТАБИЛЬНОСТЬ
# ---------------------------------------------------------
#
# Сложная привычка не требует такой же идеальности,
# как очень простая.
#
STABILITY_TARGET_BY_DIFFICULTY = {
    1: 90,
    2: 85,
    3: 80,
    4: 72,
    5: 65,
}


# ---------------------------------------------------------
# ВЕС СЛОЖНОСТИ ДЛЯ ЦЕЛИ
# ---------------------------------------------------------
#
# Это НЕ основной показатель сложности.
#
# Основная поправка уже используется внутри
# стабильности привычки.
#
# Здесь вес нужен только для объединения
# нескольких привычек одной цели.
#
DIFFICULTY_WEIGHT_BY_LEVEL = {
    1: 0.90,
    2: 0.95,
    3: 1.00,
    4: 1.05,
    5: 1.10,
}


# ---------------------------------------------------------
# ЦЕЛЬ
# ---------------------------------------------------------
#
# 45 дней — минимальный срок,
# после которого цель вообще может перейти
# в состояние "готова к проверке".
#
GOAL_MIN_DAYS = 45

# Средняя стабильность связанных привычек.
GOAL_STABILITY_TARGET = 75


# =========================================================
# НОРМАЛИЗАЦИЯ СЛОЖНОСТИ
# =========================================================

def normalize_difficulty(
    difficulty,
):
    """
    Приводит сложность к диапазону 1–5.

    Если значение отсутствует,
    используется средняя сложность = 3.
    """

    try:

        difficulty = int(
            difficulty
        )

    except (
        TypeError,
        ValueError,
    ):

        return 3

    return max(
        1,
        min(
            5,
            difficulty,
        )
    )


# =========================================================
# ДАТА СОЗДАНИЯ
# =========================================================

def parse_created_date(
    created_at,
):
    """
    Преобразует created_at в date.
    """

    if not created_at:
        return None

    if isinstance(
        created_at,
        date,
    ):

        return created_at

    text = str(
        created_at
    ).strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):

        try:

            return datetime.strptime(
                text,
                fmt,
            ).date()

        except ValueError:

            continue

    return None


# =========================================================
# СРЕДНЕЕ
# =========================================================

def calculate_average(
    values,
):
    """
    Безопасное среднее значение.
    """

    values = [
        float(value)
        for value in values
        if value is not None
    ]

    if not values:
        return None

    return round(
        sum(values)
        / len(values),
        1,
    )


# =========================================================
# СРОК ФОРМИРОВАНИЯ
# =========================================================

def get_formation_days(
    difficulty,
):
    """
    Возвращает ориентировочный срок формирования.

    1 → 21 день
    2 → 28 дней
    3 → 35 дней
    4 → 45 дней
    5 → 60 дней
    """

    difficulty = normalize_difficulty(
        difficulty
    )

    return FORMATION_DAYS_BY_DIFFICULTY[
        difficulty
    ]


# =========================================================
# ЦЕЛЕВАЯ СТАБИЛЬНОСТЬ
# =========================================================

def get_stability_target(
    difficulty,
):
    """
    Возвращает требуемую стабильность.

    1 → 90%
    2 → 85%
    3 → 80%
    4 → 72%
    5 → 65%
    """

    difficulty = normalize_difficulty(
        difficulty
    )

    return STABILITY_TARGET_BY_DIFFICULTY[
        difficulty
    ]


# =========================================================
# ВЕС СЛОЖНОСТИ
# =========================================================

def get_difficulty_weight(
    difficulty,
):
    """
    Небольшой вес сложности для объединения
    нескольких привычек в одну цель.
    """

    difficulty = normalize_difficulty(
        difficulty
    )

    return DIFFICULTY_WEIGHT_BY_LEVEL[
        difficulty
    ]


# =========================================================
# ПОЛУЧИТЬ ЛОГИ
# =========================================================

def get_habit_logs(
    habit_id,
    start_date,
    end_date,
):
    """
    Возвращает логи привычки
    за указанный период.
    """

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
        ORDER BY date ASC
        """,
        (
            habit_id,
            start_date.isoformat(),
            end_date.isoformat(),
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        row[0]: bool(
            row[1]
        )
        for row in rows
    }


# =========================================================
# ПОЛУЧИТЬ ПРИВЫЧКУ
# =========================================================

def get_habit(
    user_id,
    habit_id,
):
    """
    Получает активную привычку пользователя
    со всеми существующими PRO-полями.
    """

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
            created_at,
            formed,
            formed_at,
            last_review_date,
            controlled,
            controlled_at,
            difficulty,
            motivation,
            goal_id,
            pro_status
        FROM habits
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        LIMIT 1
        """,
        (
            habit_id,
            user_id,
        ),
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "habit_type": row[2],
        "frequency": row[3],
        "schedule_days": row[4],
        "created_at": row[5],
        "formed": bool(
            row[6]
        ),
        "formed_at": row[7],
        "last_review_date": row[8],
        "controlled": bool(
            row[9]
        ),
        "controlled_at": row[10],
        "difficulty": row[11],
        "motivation": row[12],
        "goal_id": row[13],
        "pro_status": (
            row[14]
            or "active"
        ),
    }


# =========================================================
# РАСПИСАНИЕ ПРИВЫЧКИ
# =========================================================

def is_habit_scheduled_on_date(
    habit,
    check_date,
):
    """
    Проверяет, должна ли привычка
    выполняться в конкретный день.
    """

    weekday = check_date.weekday()

    frequency = habit.get(
        "frequency"
    )

    if frequency == "daily":

        return True

    if frequency == "weekdays":

        return weekday < 5

    if frequency == "custom":

        days = habit.get(
            "schedule_days"
        )

        if not days:
            return False

        try:

            selected = {
                int(value)
                for value in str(
                    days
                ).split(",")
            }

        except (
            TypeError,
            ValueError,
        ):

            return False

        return weekday in selected

    return False


# =========================================================
# РАСЧЁТ СТАБИЛЬНОСТИ ПЕРИОДА
# =========================================================

def _calculate_period_stability(
    habit,
    logs,
    start_date,
    end_date,
):
    """
    Считает обычную стабильность за период.

    Для good:
        выполнено / запланировано

    Для bad:
        удержался / запланировано

    В текущей системе habit_logs.completed = 1
    означает желаемое поведение.
    Поэтому одна формула подходит обоим типам.
    """

    scheduled = 0
    completed = 0
    missed = 0
    pending = 0

    current = start_date

    today = date.today()

    while current <= end_date:

        if is_habit_scheduled_on_date(
            habit,
            current,
        ):

            scheduled += 1

            key = current.isoformat()

            if key in logs:

                if logs[key]:

                    completed += 1

                else:

                    missed += 1

            else:

                if current == today:

                    pending += 1

                else:

                    missed += 1

        current += timedelta(
            days=1
        )

    elapsed_scheduled = (
        completed
        + missed
    )

    if elapsed_scheduled > 0:

        stability = round(
            completed
            / elapsed_scheduled
            * 100,
            1,
        )

    else:

        stability = 0

    return {
        "scheduled": scheduled,
        "completed": completed,
        "missed": missed,
        "pending": pending,
        "elapsed_scheduled": (
            elapsed_scheduled
        ),
        "stability": stability,
    }


# =========================================================
# СТАТУС ПРИВЫЧКИ
# =========================================================

def get_formation_stage(
    formation_progress,
):
    """
    Производный статус привычки.

    Это пока НЕ записывается в БД.

    Позже эти статусы можно использовать
    для визуальной геймификации.
    """

    try:

        progress = float(
            formation_progress
        )

    except (
        TypeError,
        ValueError,
    ):

        progress = 0

    if progress < 30:

        return "Зарождение"

    if progress < 70:

        return "Формирование"

    if progress < 90:

        return "Устойчивая"

    return "Сформирована"


# =========================================================
# СТАТИСТИКА ПРИВЫЧКИ
# =========================================================

def calculate_habit_statistics(
    habit,
    today=None,
):
    """
    Главная математическая функция PRO.

    Возвращает:

    - raw_stability
    - recent_stability
    - adjusted_stability
    - difficulty
    - target_stability
    - formation_progress
    - formation_stage
    - formation_ready

    Сложность действительно влияет
    на итоговый показатель.
    """

    if today is None:

        today = date.today()

    created_date = parse_created_date(
        habit.get("created_at")
    )

    difficulty = normalize_difficulty(
        habit.get("difficulty")
    )

    target_stability = get_stability_target(
        difficulty
    )

    formation_days = get_formation_days(
        difficulty
    )

    if not created_date:

        return {
            "scheduled": 0,
            "completed": 0,
            "missed": 0,
            "pending": 0,
            "elapsed_scheduled": 0,
            "raw_stability": 0,
            "recent_stability": 0,
            "adjusted_stability": 0,
            "difficulty": difficulty,
            "target_stability": target_stability,
            "formation_days": formation_days,
            "elapsed_days": 0,
            "time_progress": 0,
            "formation_progress": 0,
            "formation_stage": "Зарождение",
            "formation_ready": False,
            "formed": bool(
                habit.get("formed")
            ),
        }

    if created_date > today:

        created_date = today

    # -----------------------------------------------------
    # ВСЯ ИСТОРИЯ
    # -----------------------------------------------------

    logs = get_habit_logs(
        habit["id"],
        created_date,
        today,
    )

    all_time = _calculate_period_stability(
        habit,
        logs,
        created_date,
        today,
    )

    # -----------------------------------------------------
    # ПОСЛЕДНИЕ 14 ДНЕЙ
    # -----------------------------------------------------

    recent_start = max(
        created_date,
        today - timedelta(
            days=RECENT_WINDOW_DAYS - 1
        ),
    )

    recent = _calculate_period_stability(
        habit,
        logs,
        recent_start,
        today,
    )

    # -----------------------------------------------------
    # СТАБИЛЬНОСТЬ
    # -----------------------------------------------------
    #
    # 70% — последние 14 дней
    # 30% — вся история
    #
    # Это делает показатель живым.
    # -----------------------------------------------------

    if (
        recent["elapsed_scheduled"] > 0
        and all_time["elapsed_scheduled"] > 0
    ):

        raw_stability = round(
            (
                recent["stability"]
                * RECENT_STABILITY_WEIGHT
            )
            +
            (
                all_time["stability"]
                * ALL_TIME_STABILITY_WEIGHT
            ),
            1,
        )

    elif all_time["elapsed_scheduled"] > 0:

        raw_stability = (
            all_time["stability"]
        )

    else:

        raw_stability = 0

    # -----------------------------------------------------
    # ПОПРАВКА НА СЛОЖНОСТЬ
    # -----------------------------------------------------
    #
    # Например:
    #
    # сложность 1 → target 90%
    # сложность 5 → target 65%
    #
    # Поэтому 75% для сложной привычки
    # будет сильнее выглядеть, чем 75%
    # для очень лёгкой.
    #
    # Итог ограничен 100%.
    # -----------------------------------------------------

    if target_stability > 0:

        adjusted_stability = round(
            min(
                100,
                (
                    raw_stability
                    / target_stability
                    * 100
                ),
            ),
            1,
        )

    else:

        adjusted_stability = 0

    # -----------------------------------------------------
    # ВРЕМЯ
    # -----------------------------------------------------

    elapsed_days = (
        today
        - created_date
    ).days + 1

    time_progress = round(
        min(
            100,
            elapsed_days
            / formation_days
            * 100,
        ),
        1,
    )

    # -----------------------------------------------------
    # ПРОГРЕСС ФОРМИРОВАНИЯ
    # -----------------------------------------------------
    #
    # 40% — время
    # 60% — стабильность
    #
    # -----------------------------------------------------

    formation_progress = round(
        (
            time_progress
            * 0.40
        )
        +
        (
            adjusted_stability
            * 0.60
        ),
        1,
    )

    # -----------------------------------------------------
    # ГОТОВНОСТЬ
    # -----------------------------------------------------
    #
    # Нельзя получить статус сформированной
    # просто из-за большого количества дней.
    #
    # Нужно:
    #
    # 1. пройти индивидуальный срок;
    # 2. иметь достаточную фактическую стабильность.
    #
    # -----------------------------------------------------

    formation_ready = (
        elapsed_days
        >= formation_days
        and all_time["elapsed_scheduled"]
        >= min(
            formation_days,
            21,
        )
        and raw_stability
        >= target_stability
    )

    # Если математически привычка уже готова,
    # её производный статус должен быть
    # "Сформирована".
    #
    # Но ручное поле formed остаётся
    # отдельным подтверждением пользователя.

    formation_stage = get_formation_stage(
        formation_progress
    )

    if formation_ready:

        formation_stage = "Сформирована"

    return {
        "scheduled": all_time[
            "scheduled"
        ],
        "completed": all_time[
            "completed"
        ],
        "missed": all_time[
            "missed"
        ],
        "pending": all_time[
            "pending"
        ],
        "elapsed_scheduled": all_time[
            "elapsed_scheduled"
        ],
        "raw_stability": raw_stability,
        "recent_stability": recent[
            "stability"
        ],
        "difficulty": difficulty,
        "target_stability": target_stability,
        "adjusted_stability": adjusted_stability,
        "formation_days": formation_days,
        "elapsed_days": elapsed_days,
        "time_progress": time_progress,
        "formation_progress": formation_progress,
        "formation_stage": formation_stage,
        "formation_ready": formation_ready,
        "formed": bool(
            habit.get("formed")
        ),
    }


# =========================================================
# ПРОГРЕСС ОДНОЙ ПРИВЫЧКИ
# =========================================================

def get_habit_progress(
    user_id,
    habit_id,
):
    """
    PRO-прогресс конкретной привычки.
    """

    if not is_pro(user_id):

        return {}

    habit = get_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return {}

    statistics = calculate_habit_statistics(
        habit
    )

    return {
        "id": habit["id"],
        "name": habit["name"],
        "type": habit["habit_type"],
        "goal_id": habit.get(
            "goal_id"
        ),
        "difficulty": statistics[
            "difficulty"
        ],
        "difficulty_target": statistics[
            "target_stability"
        ],
        "scheduled": statistics[
            "scheduled"
        ],
        "completed": statistics[
            "completed"
        ],
        "missed": statistics[
            "missed"
        ],
        "pending": statistics[
            "pending"
        ],
        "raw_stability": statistics[
            "raw_stability"
        ],
        "recent_stability": statistics[
            "recent_stability"
        ],
        "adjusted_stability": statistics[
            "adjusted_stability"
        ],
        "formation_days": statistics[
            "formation_days"
        ],
        "elapsed_days": statistics[
            "elapsed_days"
        ],
        "time_progress": statistics[
            "time_progress"
        ],
        "formation_progress": statistics[
            "formation_progress"
        ],
        "formation_stage": statistics[
            "formation_stage"
        ],
        "formation_ready": statistics[
            "formation_ready"
        ],
        "formed": statistics[
            "formed"
        ],
        "difficulty_weight": get_difficulty_weight(
            statistics["difficulty"]
        ),
    }


# =========================================================
# ВСЕ ПРИВЫЧКИ
# =========================================================

def get_all_habits_progress(
    user_id,
):
    """
    PRO-прогресс всех активных привычек.
    """

    if not is_pro(user_id):

        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id
        FROM habits
        WHERE user_id = ?
        AND active = 1
        ORDER BY id ASC
        """,
        (
            user_id,
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    result = []

    for row in rows:

        progress = get_habit_progress(
            user_id,
            row[0],
        )

        if progress:

            result.append(
                progress
            )

    return result


# =========================================================
# ПРИВЫЧКИ ЦЕЛИ
# =========================================================

def get_goal_habits(
    user_id,
    goal_id,
):
    """
    Возвращает привычки,
    связанные с конкретной целью.
    """

    if not is_pro(user_id):

        return []

    habits = get_all_habits_progress(
        user_id
    )

    return [
        habit
        for habit in habits
        if habit.get("goal_id") == goal_id
    ]


# =========================================================
# ПОЛУЧИТЬ ЦЕЛЬ
# =========================================================

def _get_goal(
    user_id,
    goal_id,
):
    """
    Получает активную цель.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            status,
            created_at,
            achieved_at
        FROM goals
        WHERE id = ?
        AND user_id = ?
        AND active = 1
        LIMIT 1
        """,
        (
            goal_id,
            user_id,
        ),
    )

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    return {
        "id": row[0],
        "title": row[1],
        "status": (
            row[2]
            or "active"
        ),
        "created_at": row[3],
        "achieved_at": row[4],
    }


# =========================================================
# ПРОГРЕСС ЦЕЛИ
# =========================================================

def calculate_goal_progress(
    user_id,
    goal_id,
):
    """
    Рассчитывает PRO-прогресс цели.

    Несколько привычек одной цели
    объединяются через взвешенное среднее.

    Вес зависит от сложности привычки,
    поэтому сложность реально участвует
    в математике цели.
    """

    if not is_pro(user_id):

        return {}

    goal = _get_goal(
        user_id,
        goal_id,
    )

    if not goal:

        return {}

    habits = get_goal_habits(
        user_id,
        goal_id,
    )

    # -----------------------------------------------------
    # НЕТ ПРИВЫЧЕК
    # -----------------------------------------------------

    if not habits:

        return {
            "goal": goal,
            "habits": [],
            "habits_count": 0,
            "average_stability": 0,
            "goal_progress": 0,
            "elapsed_days": 0,
            "time_progress": 0,
            "goal_ready": False,
            "reason": (
                "Нет привычек, связанных с целью."
            ),
        }

    # -----------------------------------------------------
    # ВЗВЕШЕННАЯ СТАБИЛЬНОСТЬ
    # -----------------------------------------------------
    #
    # Например:
    #
    # привычка 1 → 90%, вес 1.10
    # привычка 2 → 70%, вес 0.95
    # привычка 3 → 80%, вес 1.05
    #
    # Это лучше простого среднего.
    # -----------------------------------------------------

    weighted_sum = 0
    total_weight = 0

    for habit in habits:

        stability = float(
            habit.get(
                "adjusted_stability",
                0,
            )
        )

        weight = float(
            habit.get(
                "difficulty_weight",
                1.0,
            )
        )

        weighted_sum += (
            stability
            * weight
        )

        total_weight += weight

    if total_weight > 0:

        average_stability = round(
            weighted_sum
            / total_weight,
            1,
        )

    else:

        average_stability = 0

    # -----------------------------------------------------
    # ВРЕМЯ ЦЕЛИ
    # -----------------------------------------------------

    created_date = parse_created_date(
        goal.get("created_at")
    )

    today = date.today()

    if created_date:

        elapsed_days = (
            today
            - created_date
        ).days + 1

    else:

        elapsed_days = 0

    time_progress = round(
        min(
            100,
            elapsed_days
            / GOAL_MIN_DAYS
            * 100,
        ),
        1,
    )

    # -----------------------------------------------------
    # ИТОГОВЫЙ ПРОГРЕСС
    # -----------------------------------------------------
    #
    # 75% — стабильность поведения
    # 25% — время работы над целью
    #
    # -----------------------------------------------------

    goal_progress = round(
        (
            average_stability
            * 0.75
        )
        +
        (
            time_progress
            * 0.25
        ),
        1,
    )

    # -----------------------------------------------------
    # ГОТОВНОСТЬ ЦЕЛИ
    # -----------------------------------------------------
    #
    # Нужно:
    #
    # 1. минимум 45 дней;
    # 2. средняя стабильность >= 75%;
    # 3. хотя бы одна связанная привычка.
    #
    # Это НЕ означает автоматическое достижение.
    #
    # Это означает:
    #
    # "Дэн считает, что уже пора спросить пользователя".
    #
    # -----------------------------------------------------

    goal_ready = (
        elapsed_days
        >= GOAL_MIN_DAYS
        and average_stability
        >= GOAL_STABILITY_TARGET
        and len(habits) > 0
    )

    return {
        "goal": goal,
        "habits": habits,
        "habits_count": len(
            habits
        ),
        "average_stability": (
            average_stability
        ),
        "goal_stability_target": (
            GOAL_STABILITY_TARGET
        ),
        "elapsed_days": (
            elapsed_days
        ),
        "time_progress": (
            time_progress
        ),
        "goal_progress": (
            goal_progress
        ),
        "goal_ready": (
            goal_ready
        ),
    }


# =========================================================
# ВСЕ ЦЕЛИ С ПРОГРЕССОМ
# =========================================================

def get_all_goals_progress(
    user_id,
):
    """
    Возвращает PRO-прогресс всех
    активных целей.
    """

    if not is_pro(user_id):

        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id
        FROM goals
        WHERE user_id = ?
        AND active = 1
        AND status != 'achieved'
        ORDER BY is_main DESC, id ASC
        """,
        (
            user_id,
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    result = []

    for row in rows:

        progress = calculate_goal_progress(
            user_id,
            row[0],
        )

        if progress:

            result.append(
                progress
            )

    return result


# =========================================================
# СРЕДНЯЯ СТАБИЛЬНОСТЬ
# =========================================================

def get_average_habit_stability(
    user_id,
):
    """
    Средняя PRO-стабильность
    всех активных привычек.
    """

    if not is_pro(user_id):

        return 0

    habits = get_all_habits_progress(
        user_id
    )

    if not habits:

        return 0

    values = [
        habit.get(
            "adjusted_stability",
            0,
        )
        for habit in habits
    ]

    return round(
        sum(values)
        / len(values),
        1,
    )


# =========================================================
# СВОДКА PRO
# =========================================================

def get_pro_progress_summary(
    user_id,
):
    """
    Общая PRO-сводка.

    Используется недельным отчётом
    и другими аналитическими функциями.
    """

    if not is_pro(user_id):

        return {}

    habits = get_all_habits_progress(
        user_id
    )

    goals = get_all_goals_progress(
        user_id
    )

    average_stability = (
        get_average_habit_stability(
            user_id
        )
    )

    ready_habits = [
        habit
        for habit in habits
        if habit.get(
            "formation_ready"
        )
    ]

    ready_goals = [
        goal
        for goal in goals
        if goal.get(
            "goal_ready"
        )
    ]

    return {
        "average_habit_stability": (
            average_stability
        ),
        "habits_count": len(
            habits
        ),
        "goals_count": len(
            goals
        ),
        "ready_habits": ready_habits,
        "ready_goals": ready_goals,
        "habits": habits,
        "goals": goals,
    }