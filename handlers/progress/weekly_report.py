from datetime import date, datetime, timedelta

from database.progress import (
    get_progress_summary,
    get_week_stability,
    get_week_report_period,
)

from services.subscription import is_pro

from services.dan.pro_progress import (
    get_pro_progress_summary,
)


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def _safe_number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_percent(value):
    value = _safe_number(value)
    return round(value, 1)


def _signed_percent(value):
    value = _format_percent(value)

    if value > 0:
        return f"+{value}%"

    if value < 0:
        return f"{value}%"

    return "0%"


def _parse_date(value):
    if not value:
        return None

    if isinstance(value, date):
        return value

    text = str(value).strip()

    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
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
# PRO — ТЕКУЩАЯ НЕДЕЛЯ
# =========================================================

def _get_pro_weekly_data(user_id):
    """
    Собирает PRO-данные для недельного отчёта.

    Важно:
    функция полностью безопасна для FREE.
    """

    if not is_pro(user_id):
        return None

    try:
        summary = get_pro_progress_summary(
            user_id
        )

    except Exception as error:

        print(
            f"[WEEKLY PRO] "
            f"Ошибка получения PRO-прогресса: {error}"
        )

        return None

    if not summary:
        return None

    return summary


# =========================================================
# PRO — СРАВНЕНИЕ С ПРОШЛОЙ НЕДЕЛЕЙ
# =========================================================

def _calculate_previous_week_stability(
    user_id,
    current_start,
):
    """
    Получает стабильность предыдущей недели.

    Используем существующую систему weekly progress.
    Никаких изменений в БД не требуется.
    """

    if not current_start:
        return None

    start = _parse_date(
        current_start
    )

    if not start:
        return None

    previous_end = start - timedelta(
        days=1
    )

    previous_start = previous_end - timedelta(
        days=6
    )

    try:

        # Существующая функция принимает
        # пользовательский контекст текущей недели,
        # поэтому для безопасного сравнения
        # используем отдельный расчёт по данным БД.
        #
        # Если предыдущая неделя ещё отсутствует,
        # возвращаем None.

        from database.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM habit_logs
            WHERE user_id = ?
            AND date >= ?
            AND date <= ?
            """,
            (
                user_id,
                previous_start.isoformat(),
                previous_end.isoformat(),
            ),
        )

        row = cursor.fetchone()

        conn.close()

        if not row or not row[0]:
            return None

        # Сама недельная стабильность уже считается
        # существующей системой.
        #
        # Здесь намеренно не дублируем её формулу,
        # чтобы не получить две разные математики.

        try:
            from database.progress import (
                get_week_stability_for_period,
            )

            return _safe_number(
                get_week_stability_for_period(
                    user_id,
                    previous_start,
                    previous_end,
                )
            )

        except ImportError:

            return None

        except Exception:

            return None

    except Exception as error:

        print(
            f"[WEEKLY PRO] "
            f"Ошибка сравнения недель: {error}"
        )

        return None


# =========================================================
# PRO — ТЕКСТ СТАБИЛЬНОСТИ
# =========================================================

def _build_pro_stability_block(
    user_id,
    current_start,
    current_stability,
):
    """
    Красивый PRO-блок стабильности.
    """

    pro_data = _get_pro_weekly_data(
        user_id
    )

    if not pro_data:
        return ""

    average_stability = _safe_number(
        pro_data.get(
            "average_habit_stability",
            0,
        )
    )

    habits_count = int(
        _safe_number(
            pro_data.get(
                "habits_count",
                0,
            )
        )
    )

    if habits_count <= 0:
        return (
            "💎 <b>PRO-анализ привычек</b>\n\n"
            "Пока недостаточно данных по привычкам "
            "для полноценного анализа."
        )

    previous = _calculate_previous_week_stability(
        user_id,
        current_start,
    )

    if previous is not None:

        change = (
            _safe_number(
                current_stability
            )
            - previous
        )

        if change > 0:

            trend_text = (
                f"📈 За неделю стабильность выросла "
                f"на <b>{_signed_percent(change)}</b>."
            )

        elif change < 0:

            trend_text = (
                f"📉 За неделю стабильность снизилась "
                f"на <b>{abs(change):.1f}%</b>."
            )

        else:

            trend_text = (
                "➡️ Стабильность осталась примерно "
                "на том же уровне."
            )

    else:

        trend_text = (
            "🧭 Это первая неделя, с которой "
            "можно начинать сравнение."
        )

    return (
        "💎 <b>PRO-анализ привычек</b>\n\n"

        f"🔥 <b>Средняя стабильность:</b> "
        f"{average_stability:.1f}%\n"

        f"{trend_text}\n\n"

        "Это не просто процент выполненных действий. "
        "Дэн учитывает индивидуальную сложность привычек, "
        "поэтому одинаковые 70% могут означать "
        "разный результат для разных привычек."
    )


# =========================================================
# PRO — ПРИВЫЧКИ
# =========================================================

def _build_pro_habits_block(
    user_id,
):
    """
    Показывает состояние отдельных привычек.
    """

    pro_data = _get_pro_weekly_data(
        user_id
    )

    if not pro_data:
        return ""

    habits = pro_data.get(
        "habits",
        []
    )

    if not habits:
        return ""

    # Сначала самые стабильные.
    ordered = sorted(
        habits,
        key=lambda item: _safe_number(
            item.get(
                "adjusted_stability",
                0,
            )
        ),
        reverse=True,
    )

    best = ordered[0]

    worst = ordered[-1]

    best_name = (
        best.get("name")
        or "Привычка"
    )

    worst_name = (
        worst.get("name")
        or "Привычка"
    )

    best_value = _format_percent(
        best.get(
            "adjusted_stability",
            0,
        )
    )

    worst_value = _format_percent(
        worst.get(
            "adjusted_stability",
            0,
        )
    )

    text = (
        "🧩 <b>Что происходит с привычками</b>\n\n"

        f"💪 <b>Лучшая сейчас:</b>\n"
        f"«{best_name}» — {best_value}%\n\n"

        f"🎯 <b>Главная зона роста:</b>\n"
        f"«{worst_name}» — {worst_value}%"
    )

    # -----------------------------------------------------
    # СФОРМИРОВАННЫЕ ПРИВЫЧКИ
    # -----------------------------------------------------

    ready = [
        habit
        for habit in habits
        if habit.get(
            "formation_ready"
        )
    ]

    if ready:

        text += (
            "\n\n"
            "🏆 <b>Сформированные привычки:</b>\n"
        )

        for habit in ready[:3]:

            text += (
                f"• {habit.get('name', 'Привычка')}\n"
            )

        if len(ready) > 3:

            text += (
                f"• и ещё {len(ready) - 3}\n"
            )

    return text


# =========================================================
# PRO — ЦЕЛИ
# =========================================================

def _build_pro_goals_block(
    user_id,
):
    """
    Показывает связь:
    привычки → цель → прогресс.
    """

    pro_data = _get_pro_weekly_data(
        user_id
    )

    if not pro_data:
        return ""

    goals = pro_data.get(
        "goals",
        []
    )

    if not goals:
        return ""

    active_goals = [
        goal
        for goal in goals
        if goal.get("habits_count", 0) > 0
    ]

    if not active_goals:
        return ""

    text = (
        "🎯 <b>Связь привычек с целями</b>\n\n"
    )

    for goal in active_goals[:5]:

        goal_data = goal.get(
            "goal",
            {}
        )

        title = (
            goal_data.get("title")
            or "Цель"
        )

        progress = _format_percent(
            goal.get(
                "goal_progress",
                0,
            )
        )

        stability = _format_percent(
            goal.get(
                "average_stability",
                0,
            )
        )

        habits_count = goal.get(
            "habits_count",
            0,
        )

        text += (
            f"🎯 <b>{title}</b>\n"
            f"   Прогресс: {progress}%\n"
            f"   Стабильность связанных привычек: "
            f"{stability}%\n"
            f"   Привычек в связке: {habits_count}\n"
        )

        if goal.get(
            "goal_ready"
        ):

            text += (
                "   🔔 Цель уже достаточно созрела "
                "для проверки.\n"
            )

        text += "\n"

    return text.rstrip()


# =========================================================
# FREE НЕДЕЛЬНЫЙ ОТЧЁТ
# =========================================================

def generate_weekly_report(
    user_id
):

    stats = get_progress_summary(
        user_id
    )

    period_start, period_end = (
        get_week_report_period(
            user_id
        )
    )

    stability = get_week_stability(
        user_id
    )

    energy = stats["energy"]
    sleep = stats["sleep"]
    mood = stats["mood"]
    stress = stats["stress"]

    # =====================================================
    # КОЛИЧЕСТВО ДНЕЙ В ОТЧЁТЕ
    # =====================================================

    if period_start:

        start_date = date.fromisoformat(
            period_start
        )

        end_date = date.fromisoformat(
            period_end
        )

        days_passed = (
            end_date - start_date
        ).days + 1

    else:

        days_passed = 0

    # =====================================================
    # ОПРЕДЕЛЯЕМ СИЛЬНУЮ СТОРОНУ
    # =====================================================

    indicators = {

        "⚡ Энергия": energy,

        "🙂 Настрой": mood,

        "😴 Сон": sleep,

        "🧘 Контроль стресса": 10 - stress,

    }

    strong = max(
        indicators,
        key=indicators.get
    )

    weak = min(
        indicators,
        key=indicators.get
    )

    # =====================================================
    # ГЛАВНЫЙ РЕЗУЛЬТАТ
    # =====================================================

    if days_passed < 7:

        result_text = (

            f"На этой неделе у Дэна было "
            f"{days_passed} дней наблюдений.\n\n"

            "Этого ещё недостаточно для полной картины, "
            "но первые сигналы уже можно увидеть."

        )

    elif stability >= 80:

        result_text = (

            "Очень сильная неделя.\n\n"

            "Ты не просто начал выполнять действия — "
            "ты удерживал систему большую часть времени."

        )

    elif stability >= 50:

        result_text = (

            "Хорошее движение вперёд.\n\n"

            "У тебя уже появляется стабильность, "
            "но есть пространство для улучшения."

        )

    elif stability > 0:

        result_text = (

            "Неделя получилась неровной.\n\n"

            "Но главное — ты не потерял контакт с системой. "
            "Даже несколько действий лучше, чем полный отказ."

        )

    else:

        result_text = (

            "На этой неделе ритм сбился.\n\n"

            "Не нужно начинать всё заново. "
            "Просто выбери следующий маленький шаг."

        )

    # =====================================================
    # ТЕКСТ СИЛЬНОЙ СТОРОНЫ
    # =====================================================

    strong_text = {

        "⚡ Энергия":

            (
                "Твоим главным ресурсом была энергия.\n\n"

                "Когда уровень энергии выше, "
                "намного проще держать привычки "
                "и выполнять запланированные действия."
            ),

        "🙂 Настрой":

            (
                "Твоё настроение было самой стабильной частью недели.\n\n"

                "Это хороший фундамент, потому что внутреннее состояние "
                "сильно влияет на желание двигаться дальше."
            ),

        "😴 Сон":

            (
                "Сон оказался твоей сильной стороной.\n\n"

                "Хорошее восстановление помогает сохранять "
                "энергию и дисциплину."
            ),

        "🧘 Контроль стресса":

            (
                "Ты лучше всего справлялся с нагрузкой.\n\n"

                "Умение сохранять спокойствие помогает "
                "не бросать начатое."
            ),

    }.get(
        strong,
        "Ты сохранил хороший баланс в этой области."
    )

    # =====================================================
    # ТЕКСТ ЗОНЫ РОСТА
    # =====================================================

    weak_text = {

        "⚡ Энергия":

            (
                "Энергия была самым слабым местом недели.\n\n"

                "Обрати внимание на восстановление: "
                "сон, отдых и нагрузку."
            ),

        "🙂 Настрой":

            (
                "Настрой менялся сильнее всего.\n\n"

                "Попробуй добавить больше действий, "
                "которые помогают тебе чувствовать прогресс."
            ),

        "😴 Сон":

            (
                "Сон стал главной зоной внимания.\n\n"

                "Начни не с больших изменений, "
                "а с одного простого шага: "
                "например, немного раньше готовиться ко сну."
            ),

        "🧘 Контроль стресса":

            (
                "Нагрузка была самым сложным моментом недели.\n\n"

                "Попробуй добавить хотя бы короткое восстановление "
                "каждый день."
            ),

    }.get(
        weak,
        "Этой области стоит уделить немного больше внимания."
    )

    # =====================================================
    # НАБЛЮДЕНИЕ ДЭНА
    # =====================================================

    if stability < 50:

        observation = (

            "Ты пока только формируешь новый ритм.\n\n"

            "Сейчас важнее не требовать от себя идеальности, "
            "а сделать систему привычной частью жизни."

        )

    else:

        observation = (

            "Ты постепенно превращаешь действия в систему.\n\n"

            "Главное сейчас — сохранить то, что уже работает, "
            "и улучшать только один элемент за раз."

        )

    # =====================================================
    # ФОКУС
    # =====================================================

    if sleep <= 4:

        focus = (

            "Начни с восстановления сна.\n"

            "Даже небольшое улучшение режима "
            "может дать больше энергии."

        )

    elif stress >= 7:

        focus = (

            "Добавь больше восстановления.\n"

            "Не только результат важен — "
            "важно сохранять ресурс."

        )

    else:

        focus = (

            "Закрепи одну маленькую привычку.\n"

            "Стабильность важнее резких изменений."

        )

    # =====================================================
    # БАЗОВЫЙ ТЕКСТ
    # =====================================================

    text = (

        "📊 <b>Твоя неделя</b>\n\n"

        f"📅 <b>Период:</b>\n"
        f"{period_start} — {period_end}\n\n"

        "🔥 <b>Главный результат:</b>\n"
        f"{result_text}\n\n"

        "📈 <b>Стабильность:</b>\n"
        f"Ты держал систему {stability}% времени.\n\n"

        "💪 <b>Что получилось лучше всего:</b>\n"
        f"{strong}\n\n"
        f"{strong_text}\n\n"

        "🎯 <b>Главная зона внимания:</b>\n"
        f"{weak}\n\n"
        f"{weak_text}\n\n"

        "🧠 <b>Что заметил Дэн:</b>\n"
        f"{observation}\n\n"

        "⚡ <b>Фокус следующей недели:</b>\n"
        f"{focus}\n\n"

    )

    # =====================================================
    # PRO
    # =====================================================

    if is_pro(user_id):

        pro_stability = _build_pro_stability_block(
            user_id,
            period_start,
            stability,
        )

        pro_habits = _build_pro_habits_block(
            user_id
        )

        pro_goals = _build_pro_goals_block(
            user_id
        )

        if pro_stability:

            text += (
                pro_stability
                + "\n\n"
            )

        if pro_habits:

            text += (
                pro_habits
                + "\n\n"
            )

        if pro_goals:

            text += (
                pro_goals
                + "\n\n"
            )

        text += (
            "💎 <b>PRO-вывод:</b>\n\n"
            "Теперь Дэн смотрит не только на то, "
            "что ты сделал за неделю, "
            "но и на то, насколько устойчиво "
            "ты строишь систему вокруг своих целей."
            "\n\n"
        )

    # =====================================================
    # ФИНАЛ
    # =====================================================

    text += (
        "Маленькие изменения складываются "
        "в большие результаты 💪\n\n"

        "📅 Следующий отчёт Дэн подготовит "
        "в следующее воскресенье в 21:00."
    )

    return text

