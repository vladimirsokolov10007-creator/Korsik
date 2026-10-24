#!/usr/bin/env python
"""
Скрипт быстрой подготовки демо-данных для хакатона.
Создаёт тестовых пользователей, сообщения и эскалации.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Добавляем backend/app в путь
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database import Database


def seed_demo_data():
    """Заполняет БД демонстрационными данными."""
    print("Подготовка демо-данных для хакатона...")

    db = Database(settings.database_path)
    db.initialize()

    # Создаём демо-сотрудников
    users = [
        {
            "user_id": "demo_user_001",
            "display_name": "Алексей Иванов",
            "job_title": "Инженер-технолог",
            "manager_name": "Петров И.И.",
            "experience_level": "experienced",
            "location": "GrPP",
            "start_date": "2026-11-03",
            "preferred_hours": "18:30-20:00",
            "career_goal": "Стать ведущим специалистом",
            "onboarding_stage": "route_ready",
            "dialog_state": "ready",
            "consent_to_pulse": True,
        },
        {
            "user_id": "demo_user_002",
            "display_name": "Мария Петрова",
            "job_title": "Менеджер по качеству",
            "manager_name": "Сидоров А.А.",
            "experience_level": "new",
            "location": "GTP",
            "start_date": "2026-10-28",
            "preferred_hours": "19:00-20:30",
            "career_goal": "Развитие в управлении качеством",
            "onboarding_stage": "route_ready",
            "dialog_state": "ready",
            "consent_to_pulse": True,
        },
        {
            "user_id": "demo_user_003",
            "display_name": "Дмитрий Смирнов",
            "job_title": "Специалист по безопасности",
            "manager_name": "Иванова М.П.",
            "experience_level": "experienced",
            "location": "Luzhniki",
            "start_date": "2026-11-10",
            "preferred_hours": "18:00-19:30",
            "career_goal": "",
            "onboarding_stage": "registration",
            "dialog_state": "ask_start_date",
            "consent_to_pulse": False,
        },
    ]

    for user in users:
        db.upsert_user(user)
        print(f"[+] Создан пользователь: {user['display_name']}")

    # Добавляем сообщения для Алексея
    messages = [
        ("in", "/start"),
        ("out", "Здравствуйте! Я Корсик, помощник по адаптации..."),
        ("in", "Какой рабочий график?"),
        (
            "out",
            "Рабочий график — 5 дней в неделю с 9:00 до 18:00, перерыв с 13:00 до 14:00.\n\n"
            "Источник: Правила внутреннего трудового распорядка, раздел 2.1"
        ),
        ("in", "Где получить пропуск?"),
        (
            "out",
            "В утверждённых документах нет ответа на этот вопрос. Я не буду гадать.\n\n"
            "Могу подготовить обращение HR с вашим текстом: «Где получить пропуск?»"
        ),
    ]

    for direction, text in messages:
        db.save_message("demo_user_001", direction, text)

    print(f"[+] Добавлено {len(messages)} демо-сообщений")

    # Создаём эскалации
    escalations = [
        {
            "user_id": "demo_user_001",
            "reason": "Вопрос вне базы знаний",
            "message": "Где получить пропуск?",
        },
        {
            "user_id": "demo_user_002",
            "reason": "Обращение подтверждено сотрудником",
            "message": "Не могу найти документы для оформления",
        },
    ]

    for escalation in escalations:
        db.create_escalation(
            escalation["user_id"], escalation["reason"], escalation["message"]
        )

    print(f"[+] Создано {len(escalations)} эскалаций в HR")

    # Добавляем feedback для аналитики
    feedbacks = [
        {
            "user_id": "demo_user_001",
            "stage": "day_1",
            "text": "Всё понятно, спасибо!",
            "sentiment": "positive",
            "topics": ["благодарность"],
            "risk_level": "low",
        },
        {
            "user_id": "demo_user_002",
            "stage": "week_2",
            "text": "Немного запутался в процедурах",
            "sentiment": "neutral",
            "topics": ["процедуры", "путаница"],
            "risk_level": "medium",
        },
    ]

    for feedback in feedbacks:
        db.save_feedback(
            feedback["user_id"],
            feedback["stage"],
            feedback["text"],
            feedback["sentiment"],
            feedback["topics"],
            feedback["risk_level"],
        )

    print(f"[+] Добавлено {len(feedbacks)} feedback-записей")

    print("\n[OK] Демо-данные готовы!")
    print(f"База данных: {settings.database_path}")
    print("\nЗапустите сервер:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload")
    print("\nОткройте демо-чат:")
    print("   http://127.0.0.1:8000/demo/max/chat")


if __name__ == "__main__":
    seed_demo_data()
