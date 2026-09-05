from database.connection import get_connection

from database.goals import (
    create_goal,
    get_user_goals,
)

from database.habits import (
    get_user_habits,
    create_habit,
    PRO_MAX_GOOD_HABITS,
    PRO_MAX_BAD_HABITS,
)

from services.subscription import is_pro

from services.dan.pro_habits import (
    update_habit_pro_data,
    set_habit_goal,
    remove_habit_goal,
    get_habit as get_pro_habit,
)


# =========================================================
# PRO SETUP
# =========================================================

MAX_SETUP_GOALS = 3


# =========================================================
# ПРОВЕРКА PRO
# =========================================================

def can_start_pro_setup(user_id):

    try:
        return bool(
            is_pro(user_id)
        )

    except Exception:
        return False


# =========================================================
# ЦЕЛИ
# =========================================================

def get_setup_goals(user_id):

    if not can_start_pro_setup(user_id):
        return []

    return get_user_goals(
        user_id
    )


def can_add_setup_goal(user_id):

    if not can_start_pro_setup(user_id):
        return False

    goals = get_setup_goals(
        user_id
    )

    return len(goals) < MAX_SETUP_GOALS


def get_remaining_goal_slots(user_id):

    if not can_start_pro_setup(user_id):
        return 0

    goals = get_setup_goals(
        user_id
    )

    return max(
        0,
        MAX_SETUP_GOALS - len(goals)
    )


def get_setup_goal(
    user_id,
    goal_id,
):

    if not can_start_pro_setup(user_id):
        return None

    try:
        goal_id = int(
            goal_id
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    goals = get_setup_goals(
        user_id
    )

    for goal in goals:

        if goal.get("id") == goal_id:
            return goal

    return None


def add_setup_goal(
    user_id,
    title,
):

    if not can_start_pro_setup(user_id):
        return None

    title = str(
        title or ""
    ).strip()

    if not title:
        return None

    if not can_add_setup_goal(
        user_id
    ):
        return None

    return create_goal(
        user_id=user_id,
        title=title,
        is_main=False,
    )


# =========================================================
# ПРИВЫЧКИ
# =========================================================

def get_setup_habits(user_id):

    if not can_start_pro_setup(user_id):
        return []

    habits = get_user_habits(
        user_id
    )

    return sorted(
        habits,
        key=lambda habit: (
            0
            if habit.get("habit_type") == "good"
            else 1,
            habit.get("id", 0),
        )
    )


def get_current_habit(
    user_id,
    state,
):

    if not state:
        return None

    habit_id = state.get(
        "current_habit_id"
    )

    if habit_id is None:
        return None

    habits = get_setup_habits(
        user_id
    )

    for habit in habits:

        if habit.get("id") == habit_id:
            return habit

    return None


# =========================================================
# СЛОЖНОСТЬ
# =========================================================

def save_setup_difficulty(
    user_id,
    habit_id,
    difficulty,
):

    if not can_start_pro_setup(user_id):
        return False

    try:
        difficulty = int(
            difficulty
        )

    except (
        TypeError,
        ValueError,
    ):
        return False

    difficulty = max(
        1,
        min(
            5,
            difficulty,
        )
    )

    return update_habit_pro_data(
        user_id=user_id,
        habit_id=habit_id,
        difficulty=difficulty,
    )


# =========================================================
# МОТИВАЦИЯ
# =========================================================

def save_setup_motivation(
    user_id,
    habit_id,
    motivation,
):

    if not can_start_pro_setup(user_id):
        return False

    if motivation is None:
        return False

    motivation = str(
        motivation
    ).strip()

    if not motivation:
        return False

    return update_habit_pro_data(
        user_id=user_id,
        habit_id=habit_id,
        motivation=motivation,
    )


# =========================================================
# ТЕКУЩАЯ СВЯЗЬ ПРИВЫЧКИ
# =========================================================

def get_setup_habit_goal(
    user_id,
    habit_id,
):

    if not can_start_pro_setup(user_id):
        return None

    habit = get_pro_habit(
        user_id,
        habit_id,
    )

    if not habit:
        return None

    return habit.get(
        "goal_id"
    )


# =========================================================
# ПРОВЕРКА КОНФЛИКТА ЦЕЛИ
# =========================================================

def check_setup_goal_conflict(
    user_id,
    habit_id,
    goal_id,
):

    if not can_start_pro_setup(user_id):

        return {
            "allowed": False,
            "current_goal": None,
            "reason": "pro_required",
        }

    try:
        habit_id = int(
            habit_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return {
            "allowed": False,
            "current_goal": None,
            "reason": "invalid_habit",
        }

    habit = get_pro_habit(
        user_id,
        habit_id,
    )

    if not habit:

        return {
            "allowed": False,
            "current_goal": None,
            "reason": "habit_not_found",
        }

    current_goal_id = habit.get(
        "goal_id"
    )

    goals = get_setup_goals(
        user_id
    )

    current_goal = next(
        (
            goal
            for goal in goals
            if goal.get("id") == current_goal_id
        ),
        None,
    )

    # Привязки ещё нет.
    if current_goal_id is None:

        return {
            "allowed": True,
            "current_goal": None,
            "reason": None,
        }

    # Нажали ту же самую цель.
    if (
        goal_id is not None
        and current_goal_id == goal_id
    ):

        return {
            "allowed": True,
            "current_goal": current_goal,
            "reason": "same_goal",
        }

    # Уже привязана к другой цели.
    return {
        "allowed": False,
        "current_goal": current_goal,
        "reason": "already_linked",
    }


# =========================================================
# ПРИВЯЗКА К ЦЕЛИ
# =========================================================

def save_setup_goal(
    user_id,
    habit_id,
    goal_id,
):

    if not can_start_pro_setup(user_id):
        return False

    habit = get_pro_habit(
        user_id,
        habit_id,
    )

    if not habit:
        return False

    current_goal_id = habit.get(
        "goal_id"
    )

    # -----------------------------------------------------
    # УЖЕ ЕСТЬ ДРУГАЯ ЦЕЛЬ
    # -----------------------------------------------------

    if (
        current_goal_id is not None
        and goal_id != current_goal_id
    ):

        return False

    # -----------------------------------------------------
    # БЕЗ ЦЕЛИ
    # -----------------------------------------------------

    if goal_id is None:

        if current_goal_id is not None:
            return False

        return remove_habit_goal(
            user_id,
            habit_id,
        )

    # -----------------------------------------------------
    # ПРОВЕРЯЕМ ID
    # -----------------------------------------------------

    try:
        goal_id = int(
            goal_id
        )

    except (
        TypeError,
        ValueError,
    ):
        return False

    # -----------------------------------------------------
    # ПРОВЕРЯЕМ, ЧТО ЦЕЛЬ ПРИНАДЛЕЖИТ USER
    # -----------------------------------------------------

    goal = get_setup_goal(
        user_id,
        goal_id,
    )

    if not goal:
        return False

    return set_habit_goal(
        user_id=user_id,
        habit_id=habit_id,
        goal_id=goal_id,
    )


# =========================================================
# СОЗДАНИЕ НОВОЙ PRO-ПРИВЫЧКИ
# =========================================================

def create_setup_habit(
    user_id,
    name,
    habit_type,
    frequency,
    schedule_days=None,
    difficulty=None,
    motivation=None,
    goal_id=None,
):

    if not can_start_pro_setup(user_id):
        return None

    name = str(
        name or ""
    ).strip()

    if not name:
        return None

    if habit_type not in (
        "good",
        "bad",
    ):
        return None

    if frequency not in (
        "daily",
        "weekdays",
        "custom",
    ):
        return None

    # -----------------------------------------------------
    # ЛИМИТ ПРИВЫЧЕК PRO
    # -----------------------------------------------------

    existing_habits = get_user_habits(user_id)
    same_type_count = sum(
        1
        for habit in existing_habits
        if habit.get("habit_type") == habit_type
        and habit.get("pro_status") != "frozen"
    )

    max_for_type = (
        PRO_MAX_GOOD_HABITS
        if habit_type == "good"
        else PRO_MAX_BAD_HABITS
    )

    if same_type_count >= max_for_type:
        return None

    # -----------------------------------------------------
    # СЛОЖНОСТЬ
    # -----------------------------------------------------

    try:
        difficulty = int(
            difficulty
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    difficulty = max(
        1,
        min(
            5,
            difficulty,
        )
    )

    # -----------------------------------------------------
    # МОТИВАЦИЯ
    # -----------------------------------------------------

    motivation = str(
        motivation or ""
    ).strip()

    if not motivation:
        return None

    # -----------------------------------------------------
    # ЦЕЛЬ
    # -----------------------------------------------------

    if goal_id is not None:

        try:
            goal_id = int(
                goal_id
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        if not get_setup_goal(
            user_id,
            goal_id,
        ):
            return None

    # -----------------------------------------------------
    # СОЗДАЁМ ПРИВЫЧКУ
    # -----------------------------------------------------

    habit_id = create_habit(
        user_id=user_id,
        name=name,
        habit_type=habit_type,
        frequency=frequency,
        schedule_days=schedule_days,
        difficulty=difficulty,
        motivation=motivation,
    )

    if not habit_id:
        return None

    # -----------------------------------------------------
    # ПРИВЯЗЫВАЕМ К ЦЕЛИ
    # -----------------------------------------------------

    if goal_id is not None:

        save_setup_goal(
            user_id,
            habit_id,
            goal_id,
        )

    return habit_id


# =========================================================
# СОСТОЯНИЕ SETUP
# =========================================================

def create_setup_state(
    user_id,
):

    habits = get_setup_habits(
        user_id
    )

    return {
        "active": True,

        "stage": "goals",

        "habit_ids": [
            habit["id"]
            for habit in habits
        ],

        "habit_index": 0,

        "current_habit_id": (
            habits[0]["id"]
            if habits
            else None
        ),

        "current_difficulty": None,

        "current_motivation": None,

        "goals_finished": False,

        "completed_habit_ids": [],

        "new_habit": {
            "habit_type": None,
            "name": None,
            "frequency": None,
            "schedule_days": None,
            "difficulty": None,
            "motivation": None,
            "goal_id": None,
        },
    }


# =========================================================
# ПЕРЕЙТИ К СЛЕДУЮЩЕЙ ПРИВЫЧКЕ
# =========================================================

def move_to_next_habit(
    user_id,
    state,
):

    if not state:
        return False

    habits = get_setup_habits(
        user_id
    )

    current_index = state.get(
        "habit_index",
        0,
    )

    current_id = state.get(
        "current_habit_id"
    )

    if current_id is not None:

        completed = state.setdefault(
            "completed_habit_ids",
            []
        )

        if current_id not in completed:
            completed.append(
                current_id
            )

    next_index = (
        current_index + 1
    )

    if next_index >= len(habits):

        state["habit_index"] = next_index
        state["current_habit_id"] = None
        state["stage"] = "new_habits"

        return False

    next_habit = habits[
        next_index
    ]

    state["habit_index"] = next_index
    state["current_habit_id"] = next_habit["id"]

    state["current_difficulty"] = None
    state["current_motivation"] = None

    state["stage"] = "difficulty"

    return True


# =========================================================
# ПОДГОТОВКА ПОСЛЕ ЦЕЛЕЙ
# =========================================================

def prepare_setup_after_goals(
    user_id,
    state,
):

    if not state:
        return False

    habits = get_setup_habits(
        user_id
    )

    state["habit_ids"] = [
        habit["id"]
        for habit in habits
    ]

    state["habit_index"] = 0

    if not habits:

        state["current_habit_id"] = None
        state["stage"] = "new_habits"

        return False

    state["current_habit_id"] = habits[0]["id"]
    state["current_difficulty"] = None
    state["current_motivation"] = None
    state["stage"] = "difficulty"

    return True


# =========================================================
# СБРОС НОВОЙ ПРИВЫЧКИ
# =========================================================

def reset_new_habit_state(
    state,
):

    if not state:
        return

    state["new_habit"] = {
        "habit_type": None,
        "name": None,
        "frequency": None,
        "schedule_days": None,
        "difficulty": None,
        "motivation": None,
        "goal_id": None,
    }


# =========================================================
# ЗАВЕРШЕНИЕ
# =========================================================

def finish_setup(
    state,
):

    if not state:
        return

    state["active"] = False
    state["stage"] = "completed"

    state["current_habit_id"] = None
    state["current_difficulty"] = None
    state["current_motivation"] = None


def is_setup_completed(
    state,
):

    if not state:
        return False

    return (
        state.get("stage")
        == "completed"
    )