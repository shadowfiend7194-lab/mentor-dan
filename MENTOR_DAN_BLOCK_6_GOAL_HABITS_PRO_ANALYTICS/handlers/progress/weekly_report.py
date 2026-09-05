from services.dan.pro_weekly_report import build_weekly_report


def generate_weekly_report(user_id, today=None):
    text, _ = build_weekly_report(user_id, today=today)
    return text
