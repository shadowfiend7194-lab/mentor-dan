from datetime import date, datetime, timedelta

from database.connection import get_connection
from services.subscription import is_pro


# =========================================================
# PROGRESS / PRO
# =========================================================
#
# Главная задача файла:
#
# привычка
#   ↓
# выполнение
#   ↓
# сырая стабильность
#   ↓
# поправка на сложность
#   ↓
# прогресс формирования привычки
#   ↓
# привычки, связанные с целью
#   ↓
# прогресс цели
#
# ВАЖНО:
# этот файл ничего не меняет в БД.
# Он только рассчитывает показатели.
#
# =========================================================


# =========================================================
# НАСТРОЙКИ МОДЕЛИ
# =========================================================

# Минимальный срок, после которого вообще можно
# говорить о формировании привычки.
#
# 21 день — ранняя контрольная точка,
# а НЕ автоматическое формирование.
MIN_HABIT_FORMATION_DAYS = 21


# Чем сложнее привычка, тем дольше нужен период,
# чтобы считать её действительно сформированной.
#
# 1 — очень легко
# 2 — легко
# 3 — средне
# 4 — сложно
# 5 — очень сложно
#
FORMATION_DAYS_BY_DIFFICULTY = {
    1: 21,
    2: 28,
    3: 35,
    4: 45,
    5: 60,
}


# Минимальная стабильность,
# необходимая для формирования привычки.
#
# Лёгкая привычка:
# почти идеальная стабильность.
#
# Сложная привычка:
# достаточно более низкой стабильности.
#
STABILITY_TARGET_BY_DIFFICULTY = {
    1: 90,
    2: 85,
    3: 80,
    4: 72,
    5: 65,
}


# Для цели используем более длинный горизонт.
#
# 45 дней — минимальный ориентир,
# после которого цель вообще может перейти
# в состояние "готова к проверке".
GOAL_MIN_DAYS = 45


# Минимальная стабильность связанных привычек,
# чтобы предложить проверить достижение цели.
GOAL_STABILITY_TARGET = 75


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def normalize_difficulty(
    difficulty,
):
    """
    Приводит difficulty к диапазону 1–5.

    Если значение отсутствует,
    используем среднюю сложность = 3.
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


def parse_created_date(
    created_at,
):
    """
    Преобразует created_at привычки
    в date.
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


def calculate_average(
    values,
):
    """
    Среднее значение.
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
# ЦЕЛЬ ПО СЛОЖНОСТИ
# =========================================================

def get_formation_days(
    difficulty,
):
    """
    Сколько дней нужно для полноценной оценки
    формирования привычки.

    1 → 21
    2 → 28
    3 → 35
    4 → 45
    5 → 60
    """

    difficulty = normalize_difficulty(
        difficulty
    )

    return FORMATION_DAYS_BY_DIFFICULTY[
        difficulty
    ]


def get_stability_target(
    difficulty,
):
    """
    Какую стабильность считаем хорошей
    для конкретной сложности.

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
# ПОЛУЧИТЬ ЛОГИ ПРИВЫЧКИ
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
        row[0]: bool(row[1])
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
    со всеми PRO-полями.
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
        "formed": bool(row[6]),
        "formed_at": row[7],
        "last_review_date": row[8],
        "controlled": bool(row[9]),
        "controlled_at": row[10],
        "difficulty": row[11],
        "motivation": row[12],
        "goal_id": row[13],
        "pro_status": row[14] or "active",
    }


# =========================================================
# ПРОВЕРКА ДНЯ ПРИВЫЧКИ
# =========================================================

def is_habit_scheduled_on_date(
    habit,
    check_date,
):
    """
    Определяет, должна ли привычка
    выполняться в конкретный день.

    Форматы полностью соответствуют
    текущей системе habits.py.
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
# СТАТИСТИКА ПРИВЫЧКИ
# =========================================================

def calculate_habit_statistics(
    habit,
    today=None,
):
    """
    Рассчитывает всю базовую статистику
    одной привычки с момента её создания.

    Возвращает:

    - scheduled
    - completed
    - missed
    - pending
    - raw_stability
    - difficulty
    - target_stability
    - adjusted_stability
    - formation_days
    - elapsed_days
    - formation_progress
    - formation_ready
    """

    if today is None:
        today = date.today()

    created_date = parse_created_date(
        habit.get("created_at")
    )

    if not created_date:

        return {
            "scheduled": 0,
            "completed": 0,
            "missed": 0,
            "pending": 0,
            "raw_stability": 0,
            "difficulty": normalize_difficulty(
                habit.get("difficulty")
            ),
            "target_stability": get_stability_target(
                habit.get("difficulty")
            ),
            "adjusted_stability": 0,
            "formation_days": get_formation_days(
                habit.get("difficulty")
            ),
            "elapsed_days": 0,
            "formation_progress": 0,
            "formation_ready": False,
        }

    if created_date > today:

        created_date = today

    logs = get_habit_logs(
        habit["id"],
        created_date,
        today,
    )

    scheduled = 0
    completed = 0
    missed = 0
    pending = 0

    current = created_date

    while current <= today:

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

                # Сегодня ещё может быть
                # не завершённый день.
                if current == today:

                    pending += 1

                else:

                    # Старый день без лога
                    # считаем пропущенным.
                    missed += 1

        current += timedelta(
            days=1
        )

    elapsed_scheduled = (
        completed
        + missed
    )

    if elapsed_scheduled > 0:

        raw_stability = round(
            completed
            / elapsed_scheduled
            * 100,
            1,
        )

    else:

        raw_stability = 0

    difficulty = normalize_difficulty(
        habit.get("difficulty")
    )

    target_stability = (
        get_stability_target(
            difficulty
        )
    )

    formation_days = (
        get_formation_days(
            difficulty
        )
    )

    elapsed_days = (
        today
        - created_date
    ).days + 1

    # -----------------------------------------------------
    # СТАБИЛЬНОСТЬ С УЧЁТОМ СЛОЖНОСТИ
    # -----------------------------------------------------
    #
    # Принцип:
    #
    # если лёгкая привычка требует 90%,
    # то 70% = слабый результат.
    #
    # если сложная привычка требует 65%,
    # то 70% = уже хороший результат.
    #
    # Поэтому нормализуем фактическую стабильность
    # относительно индивидуального target.
    #
    # Например:
    #
    # difficulty 1:
    # 70 / 90 * 100 = 77.8
    #
    # difficulty 5:
    # 70 / 65 * 100 = 107.7 → максимум 100
    #
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
    # ПРОГРЕСС ФОРМИРОВАНИЯ
    # -----------------------------------------------------
    #
    # Смотрим одновременно:
    #
    # 1. сколько прошло времени;
    # 2. насколько стабильно выполняется привычка.
    #
    # Поэтому нельзя получить 100%
    # просто просидев нужное количество дней.
    #
    # -----------------------------------------------------

    time_progress = (
        elapsed_days
        / formation_days
        * 100
    )

    time_progress = min(
        100,
        time_progress,
    )

    formation_progress = round(
        (
            time_progress
            * 0.4
        )
        +
        (
            adjusted_stability
            * 0.6
        ),
        1,
    )

    # -----------------------------------------------------
    # ГОТОВНОСТЬ ПРИВЫЧКИ
    # -----------------------------------------------------

    formation_ready = (
        elapsed_days
        >= formation_days
        and elapsed_scheduled >= (
            min(
                formation_days,
                21,
            )
        )
        and raw_stability
        >= target_stability
    )

    return {
        "scheduled": scheduled,
        "completed": completed,
        "missed": missed,
        "pending": pending,
        "elapsed_scheduled": elapsed_scheduled,
        "raw_stability": raw_stability,
        "difficulty": difficulty,
        "target_stability": target_stability,
        "adjusted_stability": adjusted_stability,
        "formation_days": formation_days,
        "elapsed_days": elapsed_days,
        "time_progress": round(
            time_progress,
            1,
        ),
        "formation_progress": formation_progress,
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

    statistics = (
        calculate_habit_statistics(
            habit
        )
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
        "formation_ready": statistics[
            "formation_ready"
        ],
        "formed": statistics[
            "formed"
        ],
    }


# =========================================================
# ВСЕ PRO-ПРИВЫЧКИ
# =========================================================

def get_all_habits_progress(
    user_id,
):
    """
    Возвращает PRO-прогресс
    всех активных привычек пользователя.
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
# ПРИВЫЧКИ КОНКРЕТНОЙ ЦЕЛИ
# =========================================================

def get_goal_habits(
    user_id,
    goal_id,
):
    """
    Возвращает только те привычки,
    которые связаны с указанной целью.
    """

    if not is_pro(user_id):
        return []

    habits = get_all_habits_progress(
        user_id
    )

    return [
        habit
        for habit in habits
        if habit.get(
            "goal_id"
        ) == goal_id
    ]


# =========================================================
# ПРОГРЕСС ЦЕЛИ
# =========================================================

def calculate_goal_progress(
    user_id,
    goal_id,
):
    """
    Рассчитывает PRO-прогресс цели.

    Логика:

    1. Берём только связанные привычки.
    2. У каждой привычки уже есть
       стабильность с учётом сложности.
    3. Объединяем их.
    4. Проверяем срок работы над целью.
    5. Определяем готовность к проверке цели.

    """

    if not is_pro(user_id):
        return {}

    habits = get_goal_habits(
        user_id,
        goal_id,
    )

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
        return {}

    goal = {
        "id": row[0],
        "title": row[1],
        "status": row[2] or "active",
        "created_at": row[3],
        "achieved_at": row[4],
    }

    # -----------------------------------------------------
    # НЕТ ПРИВЯЗАННЫХ ПРИВЫЧЕК
    # -----------------------------------------------------

    if not habits:

        return {
            "goal": goal,
            "habits": [],
            "habits_count": 0,
            "average_stability": 0,
            "goal_progress": 0,
            "elapsed_days": 0,
            "goal_ready": False,
            "reason": (
                "Нет привычек, связанных с целью."
            ),
        }

    # -----------------------------------------------------
    # СТАБИЛЬНОСТЬ ПРИВЫЧЕК
    # -----------------------------------------------------

    stability_values = [
        habit["adjusted_stability"]
        for habit in habits
    ]

    average_stability = round(
        sum(stability_values)
        / len(stability_values),
        1,
    )

    # -----------------------------------------------------
    # ДАТА НАЧАЛА ЦЕЛИ
    # -----------------------------------------------------
    #
    # Цель сама по себе создана раньше или позже
    # привычек.
    #
    # Поэтому берём самую раннюю дату:
    #
    # goal.created_at
    #
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

    # -----------------------------------------------------
    # ВРЕМЕННОЙ ПРОГРЕСС
    # -----------------------------------------------------

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
    # ИТОГОВЫЙ ПРОГРЕСС ЦЕЛИ
    # -----------------------------------------------------
    #
    # 35% — стабильность привычек
    # 65% — фактическая стабильность.
    #
    # Важнее именно стабильность,
    # а не просто количество дней.
    #
    # -----------------------------------------------------

    stability_progress = (
        average_stability
    )

    goal_progress = round(
        (
            stability_progress
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
    # ГОТОВНОСТЬ ЦЕЛИ К ПРОВЕРКЕ
    # -----------------------------------------------------
    #
    # Нужно одновременно:
    #
    # 1. минимум 45 дней;
    # 2. средняя adjusted stability >= 75%;
    # 3. есть хотя бы одна связанная привычка;
    #
    # Тогда можно спрашивать пользователя:
    #
    # "Похоже, ты уже достаточно продвинулся.
    # Давай проверим результат."
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
    Возвращает PRO-прогресс
    всех активных целей.
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
# СРЕДНЯЯ СТАБИЛЬНОСТЬ ВСЕХ ПРИВЫЧЕК
# =========================================================

def get_average_habit_stability(
    user_id,
):
    """
    Средняя adjusted stability
    всех активных привычек пользователя.

    Это значение удобно использовать
    в недельном PRO-отчёте.
    """

    if not is_pro(user_id):
        return 0

    habits = get_all_habits_progress(
        user_id
    )

    if not habits:
        return 0

    values = [
        habit["adjusted_stability"]
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

    Её дальше можно напрямую использовать
    в недельном отчёте.
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