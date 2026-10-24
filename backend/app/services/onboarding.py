from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.database import Database


REMINDER_COPY = {
    "before_start": (
        "Завтра ваш первый рабочий день. Уточните у руководителя или HR время и место выхода, "
        "а также список документов, если его вам выдали. Не отправляйте документы и пароли в чат."
    ),
    "day_one": (
        "Как прошёл первый день? Удалось ли связаться с руководителем, понять первые задачи и уточнить, "
        "какие доступы или оборудование нужны? Если есть вопрос, опишите его — передача HR только после вашего подтверждения."
    ),
    "day_three": (
        "Вы работаете уже несколько дней. Удалось ли получить нужные доступы и понять первые задачи? "
        "Если что-то не получается, опишите ситуацию."
    ),
    "week_two": (
        "Вы в команде уже две недели. Что помогает адаптироваться, а что мешает? Ответ добровольный. "
        "Если захотите, я предложу подготовить обращение HR."
    ),
}


def reminder_time(value: str | None) -> time:
    """Reads the first HH:MM time from a user preference, with a safe default."""
    if value:
        candidate = value.replace("–", "-").split("-")[0].strip()
        try:
            return datetime.strptime(candidate, "%H:%M").time()
        except ValueError:
            pass
    return time(18, 30)


def schedule_onboarding(database: Database, user: dict[str, Any], timezone_name: str = "Europe/Moscow") -> None:
    """Schedules reminders only after the employee explicitly opted in."""
    raw_start = user.get("start_date")
    if not raw_start or not user.get("consent_to_pulse"):
        return
    start = datetime.fromisoformat(raw_start).date()
    try:
        local_tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        local_tz = ZoneInfo("UTC")
    preferred_time = reminder_time(user.get("preferred_hours"))
    notifications = {
        "before_start": datetime.combine(start - timedelta(days=1), preferred_time, tzinfo=local_tz),
        "day_one": datetime.combine(start, preferred_time, tzinfo=local_tz),
        "day_three": datetime.combine(start + timedelta(days=3), preferred_time, tzinfo=local_tz),
        "week_two": datetime.combine(start + timedelta(days=14), preferred_time, tzinfo=local_tz),
    }
    for reminder_type, due_at in notifications.items():
        database.add_reminder(user["user_id"], reminder_type, due_at.astimezone(ZoneInfo("UTC")).isoformat(), {"text": REMINDER_COPY[reminder_type]})


def employee_route(user: dict[str, Any]) -> list[dict[str, str]]:
    before_start = {
        "title": "До первого дня",
        "detail": "Уточните у руководителя или HR время и место выхода. Если вам выдали список документов, проверьте его; не отправляйте документы в чат.",
    }
    first_day = {
        "title": "В первый день",
        "detail": "Познакомьтесь с руководителем и командой, уточните первые задачи, нужные доступы и оборудование.",
    }
    if user.get("experience_level") == "new":
        return [
            before_start,
            first_day,
            {
                "title": "В первую неделю",
                "detail": "Попросите наставника или руководителя объяснить рабочие процессы и договоритесь, к кому обращаться с вопросами.",
            },
            {
                "title": "Короткие опросы о ходе адаптации",
                "detail": "Если вы включите напоминания, Корсик спросит, всё ли получается. Ответы добровольны.",
            },
        ]
    return [
        before_start,
        first_day,
        {
            "title": "В первую неделю",
            "detail": "Согласуйте приоритеты, первые результаты и формат обратной связи с руководителем.",
        },
    ]
