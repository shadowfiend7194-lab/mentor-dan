from datetime import date, datetime, timedelta
from io import BytesIO
from math import pi
from statistics import mean
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from database.connection import get_connection
from database.habits import is_habit_scheduled_on_date
from services.subscription import user_has_pro


MOSCOW = ZoneInfo("Europe/Moscow")


def _num(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values):
    values = [float(v) for v in values if v is not None]
    return round(mean(values), 1) if values else None


def _week_for(reference=None, mode="previous"):
    if reference is None:
        reference = datetime.now(MOSCOW).date()

    if mode == "current":
        start = reference - timedelta(days=reference.weekday())
        return start, reference

    # Последняя полностью завершённая Пн–Вс неделя.
    end = reference - timedelta(days=reference.weekday() + 1)
    return end - timedelta(days=6), end


def _weeks_ending(end, count=4):
    result = []
    for index in range(count):
        week_end = end - timedelta(days=7 * index)
        result.append((week_end - timedelta(days=6), week_end))
    return list(reversed(result))


def _load_checkins(user_id, start, end):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            date,
            morning_energy,
            morning_sleep,
            morning_mood,
            morning_stress,
            evening_score
        FROM checkins
        WHERE user_id = ?
          AND date BETWEEN ? AND ?
        ORDER BY date ASC
        """,
        (user_id, start.isoformat(), end.isoformat()),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "date": str(row[0])[:10],
            "energy": _num(row[1]),
            "sleep": _num(row[2]),
            "mood": _num(row[3]),
            "stress": _num(row[4]),
            "evening": _num(row[5]),
        }
        for row in rows
    ]


def _load_habits(user_id):
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
            difficulty,
            goal_id,
            motivation,
            pro_status
        FROM habits
        WHERE user_id = ?
          AND active = 1
        ORDER BY id ASC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "frequency": row[3],
            "schedule_days": row[4],
            "difficulty": row[5],
            "goal_id": row[6],
            "motivation": row[7],
            "pro_status": row[8],
        }
        for row in rows
        if row[8] != "frozen"
    ]


def _habit_week(user_id, start, end):
    habits = _load_habits(user_id)

    conn = get_connection()
    cursor = conn.cursor()
    result = []

    for habit in habits:
        cursor.execute(
            """
            SELECT date, completed
            FROM habit_logs
            WHERE habit_id = ?
              AND date BETWEEN ? AND ?
            """,
            (habit["id"], start.isoformat(), end.isoformat()),
        )

        logs = {
            str(row[0])[:10]: bool(row[1])
            for row in cursor.fetchall()
        }

        scheduled = 0
        completed = 0
        daily = {}
        current = start

        while current <= end:
            planned = is_habit_scheduled_on_date(habit, current)

            if planned:
                scheduled += 1
                completed += int(logs.get(current.isoformat(), False))
                daily[current.isoformat()] = int(
                    logs.get(current.isoformat(), False)
                )
            else:
                daily[current.isoformat()] = None

            current += timedelta(days=1)

        stability = (
            round(100 * completed / scheduled, 1)
            if scheduled
            else 0.0
        )

        result.append(
            {
                **habit,
                "scheduled": scheduled,
                "completed": completed,
                "stability": stability,
                "daily": daily,
            }
        )

    conn.close()

    active = [habit for habit in result if habit["scheduled"]]
    total_scheduled = sum(habit["scheduled"] for habit in active)
    total_completed = sum(habit["completed"] for habit in active)

    overall = (
        round(100 * total_completed / total_scheduled, 1)
        if total_scheduled
        else 0.0
    )

    return result, overall


def _daily_stability(habits, start, end):
    values = {}
    current = start

    while current <= end:
        day_values = [
            habit["daily"][current.isoformat()]
            for habit in habits
            if habit["daily"].get(current.isoformat()) is not None
        ]

        values[current.isoformat()] = (
            round(100 * mean(day_values), 1)
            if day_values
            else None
        )

        current += timedelta(days=1)

    return values


def _pearson(pairs):
    pairs = [
        (float(a), float(b))
        for a, b in pairs
        if a is not None and b is not None
    ]

    if len(pairs) < 4:
        return None

    xa = mean(x for x, _ in pairs)
    ya = mean(y for _, y in pairs)

    den_x = sum((x - xa) ** 2 for x, _ in pairs) ** 0.5
    den_y = sum((y - ya) ** 2 for _, y in pairs) ** 0.5

    if not den_x or not den_y:
        return None

    return sum(
        (x - xa) * (y - ya)
        for x, y in pairs
    ) / (den_x * den_y)


def _trend(values, minimum_delta=0.5):
    values = [v for v in values if v is not None]

    if len(values) < 2:
        return None

    delta = round(values[-1] - values[0], 1)

    if delta >= minimum_delta:
        return "растёт", delta

    if delta <= -minimum_delta:
        return "снижается", delta

    return "держится", delta


def _snapshot(user_id, start, end):
    checkins = _load_checkins(user_id, start, end)
    habits, stability = _habit_week(user_id, start, end)

    return {
        "start": start,
        "end": end,
        "checkins": checkins,
        "habits": habits,
        "stability": stability,
        "energy": _avg(row["energy"] for row in checkins),
        "sleep": _avg(row["sleep"] for row in checkins),
        "mood": _avg(row["mood"] for row in checkins),
        "stress": _avg(row["stress"] for row in checkins),
        "evening": _avg(row["evening"] for row in checkins),
        "daily": _daily_stability(habits, start, end),
    }


def _history(user_id, end):
    return [
        _snapshot(user_id, start, week_end)
        for start, week_end in _weeks_ending(end, 4)
    ]


def _habit_insights(current, previous):
    active = [
        habit
        for habit in current["habits"]
        if habit["scheduled"]
    ]

    if not active:
        return []

    insights = []

    best = max(active, key=lambda habit: habit["stability"])
    worst = min(active, key=lambda habit: habit["stability"])

    if (
        best["id"] != worst["id"]
        and best["stability"] - worst["stability"] >= 20
    ):
        insights.append(
            f"«{best['name']}» держится на {best['stability']:.0f}%, "
            f"а «{worst['name']}» — на {worst['stability']:.0f}%. "
            "Слабое звено сейчас важнее новой привычки."
        )

    if previous:
        previous_by_id = {
            habit["id"]: habit
            for habit in previous["habits"]
        }

        movers = []

        for habit in active:
            old = previous_by_id.get(habit["id"])

            if old:
                delta = habit["stability"] - old["stability"]

                if abs(delta) >= 15:
                    movers.append((habit, delta))

        if movers:
            habit, delta = max(
                movers,
                key=lambda item: abs(item[1])
            )

            insights.append(
                f"Самое заметное изменение — «{habit['name']}»: "
                f"{delta:+.0f}% к стабильности относительно прошлой недели."
            )

    return insights[:2]


def _correlation_insights(checkins):
    insights = []

    sleep_energy = _pearson(
        (row["sleep"], row["energy"])
        for row in checkins
    )

    stress_energy = _pearson(
        (row["stress"], row["energy"])
        for row in checkins
    )

    energy_mood = _pearson(
        (row["energy"], row["mood"])
        for row in checkins
    )

    if sleep_energy is not None and abs(sleep_energy) >= 0.45:
        direction = "выше" if sleep_energy > 0 else "ниже"

        insights.append(
            f"Сон и энергия заметно связаны (r={sleep_energy:+.2f}): "
            f"в дни с {direction} сном энергия чаще двигалась в ту же сторону."
        )

    if stress_energy is not None and stress_energy <= -0.45:
        insights.append(
            f"Стресс и энергия идут в разные стороны "
            f"(r={stress_energy:+.2f}): в более напряжённые дни "
            "энергия чаще проседала."
        )

    if energy_mood is not None and energy_mood >= 0.55:
        insights.append(
            f"Энергия и настроение заметно совпадали по движению "
            f"(r={energy_mood:+.2f})."
        )

    return insights[:2]


def _specific_focus(current, previous):
    active = [
        habit
        for habit in current["habits"]
        if habit["scheduled"]
    ]

    worst = min(
        active,
        key=lambda habit: habit["stability"],
        default=None,
    )

    if previous:
        delta = current["stability"] - previous["stability"]

        if delta <= -15:
            if worst:
                return (
                    f"Верни ритм на «{worst['name']}». Она просела сильнее всего, "
                    "поэтому на следующей неделе не добавляй новую нагрузку, "
                    "а добейся заметного восстановления этой привычки."
                )

            return (
                "Неделя заметно просела. На следующей неделе задача — "
                "восстановить базовый ритм, а не усложнять систему."
            )

        if delta >= 15:
            return (
                "Не пытайся сразу поднять планку. Закрепи ритм, "
                "который уже начал работать, и проверь, выдержится ли он "
                "ещё одну неделю."
            )

    if current["sleep"] is not None and current["sleep"] <= 5.5:
        return (
            "Главный рычаг — сон: выровняй время отхода ко сну "
            "и посмотри, изменится ли вместе с ним энергия."
        )

    if current["stress"] is not None and current["stress"] >= 7:
        return (
            "Главный рычаг — перегрузка: оставь обязательный минимум "
            "по привычкам и убери одну лишнюю задачу."
        )

    if worst and worst["stability"] < 60:
        return (
            f"Главный рычаг — «{worst['name']}»: поставь её в центр недели "
            "и сначала добейся устойчивости, а не идеального результата."
        )

    if worst:
        return (
            f"Главный рычаг — «{worst['name']}»: это сейчас самая слабая "
            "часть системы. Не добавляй новую привычку, пока не подтянешь её ритм."
        )

    return (
        "Продолжи отмечать неделю. Следующий отчёт сможет отделить "
        "закономерность от случайного колебания."
    )


def _trend_lines(history):
    specs = [
        ("stability", "Стабильность", 5),
        ("energy", "Энергия", 0.5),
        ("sleep", "Сон", 0.5),
        ("mood", "Настрой", 0.5),
        ("stress", "Стресс", 0.5),
    ]

    result = []

    for key, title, threshold in specs:
        trend = _trend(
            [snapshot[key] for snapshot in history],
            threshold,
        )

        if not trend:
            continue

        word, delta = trend

        # Для стресса снижение — хороший знак, поэтому
        # направление отображаем не только математически.
        if key == "stress":
            if word == "снижается":
                marker = "↓"
                meaning = "лучше"
            elif word == "растёт":
                marker = "↑"
                meaning = "хуже"
            else:
                marker = "→"
                meaning = "стабильно"
        else:
            marker = (
                "↑" if word == "растёт"
                else "↓" if word == "снижается"
                else "→"
            )
            meaning = word

        result.append(
            {
                "key": key,
                "title": title,
                "word": word,
                "delta": delta,
                "marker": marker,
                "meaning": meaning,
                "text": f"{marker} {title}: {meaning} ({delta:+.1f})",
            }
        )

    return result


def _radar(snapshot, trend_lines, focus):
    labels = [
        "Стабильность",
        "Энергия",
        "Сон",
        "Настрой",
        "Контроль стресса",
    ]

    values = [
        max(0, min(100, snapshot["stability"])),
        max(0, min(100, snapshot["energy"] * 10))
        if snapshot["energy"] is not None
        else 0,
        max(0, min(100, snapshot["sleep"] * 10))
        if snapshot["sleep"] is not None
        else 0,
        max(0, min(100, snapshot["mood"] * 10))
        if snapshot["mood"] is not None
        else 0,
        max(0, min(100, 100 - snapshot["stress"] * 10))
        if snapshot["stress"] is not None
        else 0,
    ]

    angles = [
        2 * pi * index / len(labels)
        for index in range(len(labels))
    ]

    closed_angles = angles + [angles[0]]
    closed_values = values + [values[0]]

    fig = plt.figure(figsize=(11, 8.5), dpi=180)
    fig.patch.set_facecolor("#0b0d12")

    # -----------------------------
    # RADAR
    # -----------------------------

    ax = fig.add_axes(
        [0.055, 0.18, 0.52, 0.62],
        polar=True,
    )
    ax.set_facecolor("#11151d")
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 100)
    ax.spines["polar"].set_visible(False)

    ax.set_xticks(angles)
    ax.set_xticklabels(
        labels,
        fontsize=10,
        color="#e8ebf2",
        fontweight="bold",
    )

    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(
        ["25", "50", "75", "100"],
        fontsize=7,
        color="#686f80",
    )

    ax.grid(
        color="#3b414f",
        alpha=0.55,
        linewidth=0.8,
    )

    ax.plot(
        closed_angles,
        [25] * len(closed_angles),
        color="#2a303c",
        linewidth=0.7,
    )
    ax.plot(
        closed_angles,
        [50] * len(closed_angles),
        color="#2a303c",
        linewidth=0.7,
    )
    ax.plot(
        closed_angles,
        [75] * len(closed_angles),
        color="#2a303c",
        linewidth=0.7,
    )
    ax.plot(
        closed_angles,
        [100] * len(closed_angles),
        color="#2a303c",
        linewidth=0.7,
    )

    ax.plot(
        closed_angles,
        closed_values,
        color="#9b8cff",
        linewidth=3,
        marker="o",
        markersize=6,
        markerfacecolor="#f3f1ff",
        markeredgecolor="#9b8cff",
        markeredgewidth=1.5,
    )

    ax.fill(
        closed_angles,
        closed_values,
        color="#8c7cff",
        alpha=0.24,
    )

    # -----------------------------
    # HEADER
    # -----------------------------

    fig.text(
        0.055,
        0.945,
        "ДЭН  /  PRO WEEKLY",
        fontsize=10,
        color="#9b8cff",
        fontweight="bold",
    )

    fig.text(
        0.055,
        0.900,
        "Твой недельный профиль",
        fontsize=25,
        color="#f5f7fb",
        fontweight="bold",
    )

    fig.text(
        0.055,
        0.865,
        f"{snapshot['start'].strftime('%d.%m')} — "
        f"{snapshot['end'].strftime('%d.%m.%Y')}",
        fontsize=11,
        color="#9ba1af",
    )

    # -----------------------------
    # RIGHT INFO PANEL
    # -----------------------------

    panel = FancyBboxPatch(
        (0.62, 0.18),
        0.325,
        0.62,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        transform=fig.transFigure,
        facecolor="#11151d",
        edgecolor="#252b36",
        linewidth=1,
    )
    fig.add_artist(panel)

    fig.text(
        0.65,
        0.755,
        "НЕДЕЛЯ",
        fontsize=8,
        color="#737b8b",
        fontweight="bold",
    )

    fig.text(
        0.65,
        0.710,
        f"{snapshot['stability']:.0f}%",
        fontsize=30,
        color="#f5f7fb",
        fontweight="bold",
    )

    fig.text(
        0.65,
        0.675,
        "стабильность привычек",
        fontsize=9,
        color="#a1a7b4",
    )

    fig.text(
        0.65,
        0.615,
        "ТЕНДЕНЦИИ",
        fontsize=8,
        color="#737b8b",
        fontweight="bold",
    )

    y = 0.575
    for item in trend_lines[:5]:
        fig.text(
            0.65,
            y,
            item["text"],
            fontsize=9.2,
            color="#e2e5ec",
        )
        y -= 0.045

    fig.text(
        0.65,
        0.345,
        "ФОКУС СЛЕДУЮЩЕЙ НЕДЕЛИ",
        fontsize=8,
        color="#737b8b",
        fontweight="bold",
    )

    # Переносим длинный совет по словам.
    words = focus.split()
    focus_lines = []
    line = ""

    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) > 34 and line:
            focus_lines.append(line)
            line = word
        else:
            line = candidate

    if line:
        focus_lines.append(line)

    for index, line in enumerate(focus_lines[:6]):
        fig.text(
            0.65,
            0.310 - index * 0.032,
            line,
            fontsize=8.4,
            color="#cdd1da",
        )

    # -----------------------------
    # FOOTER
    # -----------------------------

    fig.text(
        0.055,
        0.075,
        "5 показателей · 100 = сильная сторона",
        fontsize=8.5,
        color="#6f7686",
    )

    fig.text(
        0.945,
        0.075,
        "ДЭН · DISCIPLINE MENTOR",
        fontsize=8.5,
        color="#6f7686",
        ha="right",
        fontweight="bold",
    )

    output = BytesIO()
    output.name = "dan_pro_weekly_radar.png"

    fig.savefig(
        output,
        format="png",
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        pad_inches=0.25,
    )

    plt.close(fig)
    output.seek(0)

    return output


def build_weekly_report(user_id, today=None, week_mode="previous"):
    if not user_has_pro(user_id):
        return None, None

    start, end = _week_for(today, mode=week_mode)

    current = _snapshot(
        user_id,
        start,
        end,
    )

    history = _history(
        user_id,
        end,
    )

    previous = (
        history[-2]
        if len(history) >= 2
        else None
    )

    trend_lines = _trend_lines(history)
    focus = _specific_focus(
        current,
        previous,
    )

    total_completed = sum(
        habit["completed"]
        for habit in current["habits"]
    )

    total_scheduled = sum(
        habit["scheduled"]
        for habit in current["habits"]
    )

    lines = [
        "💎 <b>PRO-отчёт Дэна</b>",
        "",
        f"📅 <b>Период:</b> "
        f"{start.strftime('%d.%m')} — {end.strftime('%d.%m.%Y')}",
        f"🕒 <b>Сформирован:</b> "
        f"{datetime.now(MOSCOW).strftime('%d.%m.%Y %H:%M')}",
        "",
        "🧠 <b>Итог недели</b>",
        "",
    ]

    if total_scheduled:
        lines.append(
            f"🔥 Стабильность привычек — "
            f"<b>{current['stability']:.1f}%</b> "
            f"({total_completed}/{total_scheduled} выполнений)."
        )
    else:
        lines.append(
            "По привычкам пока нет достаточно запланированных "
            "действий для честной оценки."
        )

    if previous and total_scheduled:
        delta = current["stability"] - previous["stability"]
        lines.append(
            f"📊 Относительно прошлой недели: <b>{delta:+.1f} п.п.</b>."
        )

    if current["checkins"]:
        lines += [
            "",
            "❤️ <b>Состояние</b>",
            "",
            f"⚡ Энергия — <b>{current['energy'] if current['energy'] is not None else '—'}/10</b>",
            f"😴 Сон — <b>{current['sleep'] if current['sleep'] is not None else '—'}/10</b>",
            f"🙂 Настрой — <b>{current['mood'] if current['mood'] is not None else '—'}/10</b>",
            f"😰 Стресс — <b>{current['stress'] if current['stress'] is not None else '—'}/10</b>",
        ]

    lines += [
        "",
        "📈 <b>Тенденции за последние 4 недели</b>",
    ]

    if trend_lines:
        lines.extend(
            f"• {item['text']}"
            for item in trend_lines
        )
    else:
        lines.append(
            "• Пока недостаточно данных для устойчивой тенденции."
        )

    active = [
        habit
        for habit in current["habits"]
        if habit["scheduled"]
    ]

    if active:
        lines += [
            "",
            "🔥 <b>Привычки</b>",
        ]

        for habit in sorted(
            active,
            key=lambda item: item["stability"],
            reverse=True,
        )[:5]:
            icon = "🟢" if habit["type"] == "good" else "🔴"

            lines.append(
                f"{icon} {habit['name']} — "
                f"<b>{habit['stability']:.0f}%</b> "
                f"({habit['completed']}/{habit['scheduled']})"
            )

    insights = (
        _habit_insights(current, previous)
        + _correlation_insights(current["checkins"])
    )

    if insights:
        lines += [
            "",
            "🔎 <b>Что заметил Дэн</b>",
        ]
        lines.extend(
            f"• {insight}"
            for insight in insights[:4]
        )

    daily_values = [
        value
        for value in current["daily"].values()
        if value is not None
    ]

    if len(daily_values) >= 4:
        midpoint = max(
            2,
            len(daily_values) // 2,
        )

        first = mean(daily_values[:midpoint])
        second = mean(daily_values[midpoint:])

        if abs(second - first) >= 0.12:
            direction = (
                "усилился"
                if second > first
                else "просел"
            )

            lines.append(
                ""
                f"📅 <b>Ритм недели:</b> к концу недели "
                f"он {direction} примерно на "
                f"{abs(second - first):.0f} п.п."
            )

    lines += [
        "",
        "🎯 <b>Совет Дэна на следующую неделю</b>",
        focus,
        "",
        "Один точный рычаг на неделю полезнее пяти новых обещаний себе.",
    ]

    chart = _radar(
        current,
        trend_lines,
        focus,
    )

    return "\n".join(lines), chart
