from datetime import datetime, date, timedelta

from database.connection import get_connection
from database.events import add_event


# =========================================================
# СПИСОК ДОСТИЖЕНИЙ
# =========================================================

ACHIEVEMENTS = [

    {
        "key": "first_step",
        "category": "🚀 Начало пути",
        "title": "Первый шаг",
        "emoji": "🌱",
        "condition": "Завершить первый чек-ин.",
        "description": "С малого начинается большое.",
    },

    {
        "key": "full_day",
        "category": "🚀 Начало пути",
        "title": "Ориентир найден",
        "emoji": "🧭",
        "condition": "Пройти утренний и вечерний чек-ин в один день.",
        "description": (
            "Ты увидел весь день целиком — "
            "от его начала до его завершения."
        ),
    },

    {
        "key": "first_rhythm",
        "category": "🚀 Начало пути",
        "title": "Первый ритм",
        "emoji": "🔥",
        "condition": "Пройти чек-ины в течение 3 разных дней.",
        "description": "Ты уже возвращаешься сюда не случайно.",
    },

    {
        "key": "morning_rhythm",
        "category": "☀️🌙 Ритм",
        "title": "Встречай день",
        "emoji": "☀️",
        "condition": "Завершить 7 утренних чек-инов.",
        "description": "Ты начал встречать день осознанно.",
    },

    {
        "key": "evening_rhythm",
        "category": "☀️🌙 Ритм",
        "title": "Закрывай день",
        "emoji": "🌙",
        "condition": "Завершить 7 вечерних чек-инов.",
        "description": "Умеешь не только начинать, но и подводить итог.",
    },

    {
        "key": "checkin_7",
        "category": "☀️🌙 Ритм",
        "title": "Вошёл в ритм",
        "emoji": "🔥",
        "condition": "7 дней подряд с выполненным чек-ином.",
        "description": "Ритм начинает работать на тебя.",
    },

    {
        "key": "checkin_14",
        "category": "☀️🌙 Ритм",
        "title": "На волне",
        "emoji": "⚡",
        "condition": "14 дней подряд с выполненным чек-ином.",
        "description": "Уже похоже на новую привычку.",
    },

    {
        "key": "checkin_30",
        "category": "☀️🌙 Ритм",
        "title": "Без сбоев",
        "emoji": "🛡",
        "condition": "30 дней подряд с выполненным чек-ином.",
        "description": "Стабильность сильнее мотивации.",
    },

    {
        "key": "good_habit_7",
        "category": "✅ Полезные привычки",
        "title": "Держу слово",
        "emoji": "🌿",
        "condition": "Полезная привычка выполнена 7 дней подряд.",
        "description": "Ты сказал — ты сделал.",
    },

    {
        "key": "good_habit_14",
        "category": "✅ Полезные привычки",
        "title": "Вошло в систему",
        "emoji": "🔥",
        "condition": "Полезная привычка выполнена 14 дней подряд.",
        "description": (
            "То, что требовало усилий, "
            "начинает становиться естественным."
        ),
    },

    {
        "key": "good_habit_30",
        "category": "✅ Полезные привычки",
        "title": "Это уже твоё",
        "emoji": "👑",
        "condition": "Полезная привычка выполнена 30 дней подряд.",
        "description": (
            "Ты уже не просто стараешься — "
            "ты живёшь по-новому."
        ),
    },

    {
        "key": "bad_habit_7",
        "category": "🚫 Плохие привычки",
        "title": "Первый барьер",
        "emoji": "🧱",
        "condition": "7 дней подряд без плохой привычки.",
        "description": "Ты уже умеешь сказать себе «нет».",
    },

    {
        "key": "bad_habit_14",
        "category": "🚫 Плохие привычки",
        "title": "Разрывая цепь",
        "emoji": "⛓",
        "condition": "14 дней подряд без плохой привычки.",
        "description": "Старый сценарий больше не управляет тобой.",
    },

    {
        "key": "bad_habit_30",
        "category": "🚫 Плохие привычки",
        "title": "Стальная выдержка",
        "emoji": "🗿",
        "condition": "30 дней подряд без плохой привычки.",
        "description": "Сила — это контроль над собой.",
    },

        {
        "key": "first_goal_achieved",
        "category": "🏆 Твои результаты",
        "title": "Сказано — сделано",
        "emoji": "🎯",
        "condition": "Впервые достичь поставленной цели.",
        "description": (
            "Ты не просто поставил цель — "
            "ты довёл её до результата."
        ),
    },

    {
        "key": "first_good_habit_formed",
        "category": "🏆 Твои результаты",
        "title": "Пошло в привычку",
        "emoji": "🌱",
        "condition": "Впервые сформировать полезную привычку.",
        "description": (
            "То, что раньше требовало усилий, "
            "стало частью твоего ритма."
        ),
    },

    {
        "key": "first_bad_habit_controlled",
        "category": "🏆 Твои результаты",
        "title": "Что было, то прошло",
        "emoji": "🛡️",
        "condition": "Впервые оставить плохую привычку в прошлом.",
        "description": (
            "Ты оставил старую привычку позади. "
            "Теперь решения принимаешь ты, а не она."
        ),
    },


    {
        "key": "iron_character",
        "category": "✨ Редкие",
        "title": "Железный характер",
        "emoji": "🦾",
        "condition": "100 дней реальной активности с Дэном.",
        "description": (
            "Ты уже не просто работаешь над собой. "
            "Ты меняешь образ жизни."
        ),
    },

]


# =========================================================
# СОЗДАТЬ ТАБЛИЦУ ДОСТИЖЕНИЙ
# =========================================================

def ensure_achievement_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_achievements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            achievement_key TEXT NOT NULL,

            earned_at TEXT NOT NULL,

            UNIQUE(
                user_id,
                achievement_key
            )

        )
        """
    )

    conn.commit()
    conn.close()


# =========================================================
# ПРОВЕРКА ПЛОХОЙ ПРИВЫЧКИ
# =========================================================

def is_bad_habit_type(
    habit_type
):

    value = str(
        habit_type
    ).strip().lower()

    return value in {
        "bad",
        "negative",
        "bad_habit",
        "negative_habit",
        "плохая",
        "плохая привычка",
    }


# =========================================================
# КОЛИЧЕСТВО ЧЕК-ИНОВ
# =========================================================

def get_checkin_stats(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            COUNT(DISTINCT date)

        FROM checkin_history

        WHERE
            user_id = ?
            AND completed = 1
        """,
        (
            user_id,
        )
    )

    total, active_days = cursor.fetchone()

    cursor.execute(
        """
        SELECT COUNT(DISTINCT date)

        FROM checkin_history

        WHERE
            user_id = ?
            AND type = 'morning'
            AND completed = 1
        """,
        (
            user_id,
        )
    )

    morning_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT date)

        FROM checkin_history

        WHERE
            user_id = ?
            AND type = 'evening'
            AND completed = 1
        """,
        (
            user_id,
        )
    )

    evening_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT date

        FROM checkin_history

        WHERE
            user_id = ?
            AND completed = 1

        GROUP BY date

        HAVING COUNT(DISTINCT type) >= 2

        LIMIT 1
        """,
        (
            user_id,
        )
    )

    full_day = cursor.fetchone() is not None

    conn.close()

    return {
        "total": total,
        "active_days": active_days,
        "morning_count": morning_count,
        "evening_count": evening_count,
        "full_day": full_day,
    }


# =========================================================
# ТЕКУЩАЯ СЕРИЯ ЧЕК-ИНОВ
# =========================================================

def get_checkin_streak(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT date

        FROM checkin_history

        WHERE
            user_id = ?
            AND completed = 1
        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    completed_dates = {
        date.fromisoformat(row[0])
        for row in rows
    }

    streak = 0
    current = date.today()

    while current in completed_dates:

        streak += 1

        current -= timedelta(
            days=1
        )

    return streak


# =========================================================
# СЕРИЯ ПОЛЕЗНОЙ ПРИВЫЧКИ
# =========================================================

def get_best_good_habit_streak(
    user_id
):

    from database.habits import get_user_habits, get_habit_streak

    habits = get_user_habits(
        user_id
    )

    best = 0

    for habit in habits:

        if is_bad_habit_type(
            habit.get("habit_type")
        ):
            continue

        streak = get_habit_streak(
            habit["id"]
        )

        if streak > best:
            best = streak

    return best


# =========================================================
# СЕРИЯ ВОЗДЕРЖАНИЯ ОТ ПЛОХОЙ ПРИВЫЧКИ
# =========================================================

def get_best_bad_habit_abstinence(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            habit_type,
            frequency,
            schedule_days,
            created_at

        FROM habits

        WHERE
            user_id = ?
            AND active = 1
        """,
        (
            user_id,
        )
    )

    habits = cursor.fetchall()

    best = 0

    for habit in habits:

        (
            habit_id,
            habit_type,
            frequency,
            schedule_days,
            created_at
        ) = habit

        if not is_bad_habit_type(
            habit_type
        ):
            continue

        try:

            created_date = (
                datetime.fromisoformat(
                    created_at
                ).date()
            )

        except (TypeError, ValueError):

            created_date = date.today()


        streak = 0
        current = date.today()

        while current >= created_date:

            weekday = current.weekday()

            scheduled = False

            if frequency == "daily":

                scheduled = True

            elif frequency == "weekdays":

                scheduled = weekday < 5

            elif frequency == "custom":

                if schedule_days:

                    try:

                        selected = {
                            int(x)
                            for x in str(
                                schedule_days
                            ).split(",")
                        }

                        scheduled = (
                            weekday in selected
                        )

                    except (TypeError, ValueError):

                        scheduled = False

            if not scheduled:

                current -= timedelta(
                    days=1
                )

                continue


            cursor.execute(
                """
                SELECT completed

                FROM habit_logs

                WHERE
                    habit_id = ?
                    AND date = ?

                """,
                (
                    habit_id,
                    current.isoformat()
                )
            )

            row = cursor.fetchone()

            completed = (
                bool(row[0])
                if row
                else False
            )

            if completed:

                break

            streak += 1

            current -= timedelta(
                days=1
            )

        best = max(
            best,
            streak
        )

    conn.close()

    return best


# =========================================================
# РЕАЛЬНАЯ АКТИВНОСТЬ
# =========================================================

def get_active_days(
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT date

        FROM checkin_history

        WHERE
            user_id = ?
            AND completed = 1

        """,
        (
            user_id,
        )
    )

    dates = {
        row[0]
        for row in cursor.fetchall()
    }

    cursor.execute(
        """
        SELECT DISTINCT hl.date

        FROM habit_logs hl

        JOIN habits h
        ON h.id = hl.habit_id

        WHERE
            h.user_id = ?
            AND hl.completed = 1

        """,
        (
            user_id,
        )
    )

    dates.update(
        row[0]
        for row in cursor.fetchall()
    )

    conn.close()

    return len(dates)


# =========================================================
# ПОЛУЧИТЬ ПОЛУЧЕННЫЕ ДОСТИЖЕНИЯ
# =========================================================

def get_earned_keys(
    user_id
):

    ensure_achievement_table()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT achievement_key

        FROM user_achievements

        WHERE user_id = ?

        """,
        (
            user_id,
        )
    )

    keys = {
        row[0]
        for row in cursor.fetchall()
    }

    conn.close()

    return keys


# =========================================================
# ПРОВЕРКА И ВЫДАЧА ДОСТИЖЕНИЙ
# =========================================================

async def check_and_award_achievements(
    update,
    context
):

    ensure_achievement_table()

    user_id = update.effective_user.id

    stats = get_checkin_stats(
        user_id
    )

    checkin_streak = get_checkin_streak(
        user_id
    )

    good_streak = get_best_good_habit_streak(
        user_id
    )

    bad_streak = get_best_bad_habit_abstinence(
        user_id
    )

    active_days = get_active_days(
        user_id
    )
    
    # =====================================================
    # ДОСТИЖЕНИЯ ЦЕЛЕЙ И ПРИВЫЧЕК
    # =====================================================

    conn = get_connection()
    cursor = conn.cursor()

    # Достигнута ли хотя бы одна цель
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM goals
        WHERE user_id = ?
        AND status = 'achieved'
        """,
        (
            user_id,
        )
    )

    achieved_goals = cursor.fetchone()[0] > 0


    # Сформирована ли хотя бы одна хорошая привычка
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM habits
        WHERE user_id = ?
        AND active = 1
        AND habit_type = 'good'
        AND formed = 1
        """,
        (
            user_id,
        )
    )

    formed_good_habits = (
        cursor.fetchone()[0] > 0
    )


    # Переведена ли хотя бы одна плохая привычка
    # в состояние "под контролем"
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM habits
        WHERE user_id = ?
        AND active = 1
        AND habit_type = 'bad'
        AND controlled = 1
        """,
        (
            user_id,
        )
    )

    controlled_bad_habits = (
        cursor.fetchone()[0] > 0
    )

    conn.close()

    earned = get_earned_keys(
        user_id
    )

    conditions = {

        "first_step":
            stats["total"] >= 1,

        "full_day":
            stats["full_day"],

        "first_rhythm":
            stats["active_days"] >= 3,

        "morning_rhythm":
            stats["morning_count"] >= 7,

        "evening_rhythm":
            stats["evening_count"] >= 7,

        "checkin_7":
            checkin_streak >= 7,

        "checkin_14":
            checkin_streak >= 14,

        "checkin_30":
            checkin_streak >= 30,

        "good_habit_7":
            good_streak >= 7,

        "good_habit_14":
            good_streak >= 14,

        "good_habit_30":
            good_streak >= 30,

        "bad_habit_7":
            bad_streak >= 7,

        "bad_habit_14":
            bad_streak >= 14,

        "bad_habit_30":
            bad_streak >= 30,
                
        "first_goal_achieved":
            achieved_goals,

        "first_good_habit_formed":
            formed_good_habits,

        "first_bad_habit_controlled":
            controlled_bad_habits,

        "iron_character":
            active_days >= 100,

    }

    new_achievements = []

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for achievement in ACHIEVEMENTS:

        key = achievement["key"]

        if key in earned:
            continue

        if not conditions.get(
            key,
            False
        ):
            continue

        cursor.execute(
            """
            INSERT OR IGNORE INTO user_achievements
            (
                user_id,
                achievement_key,
                earned_at
            )

            VALUES (?, ?, ?)
            """,
            (
                user_id,
                key,
                now
            )
        )

        if cursor.rowcount == 1:

            new_achievements.append(
                achievement
            )

    conn.commit()
    conn.close()

    # =====================================================
    # УВЕДОМЛЕНИЯ И ИСТОРИЯ
    # =====================================================

    for achievement in new_achievements:

        add_event(
            user_id=user_id,
            event_type=(
                f"achievement_{achievement['key']}"
            ),
            title=(
                f"Получил достижение "
                f"«{achievement['title']}»"
            ),
            description=(
                achievement["description"]
            )
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🏆 <b>Достижение получено!</b>\n\n"
                f"{achievement['emoji']} "
                f"<b>{achievement['title']}</b>\n\n"
                f"{achievement['description']}"
            ),
            parse_mode="HTML"
        )


# =========================================================
# СТАТУС ДОСТИЖЕНИЙ ДЛЯ ЭКРАНА
# =========================================================

def get_achievements_status(
    user_id
):

    earned = get_earned_keys(
        user_id
    )

    result = []

    for achievement in ACHIEVEMENTS:

        item = dict(
            achievement
        )

        item["earned"] = (
            achievement["key"]
            in earned
        )

        result.append(
            item
        )

    return result