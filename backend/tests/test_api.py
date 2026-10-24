from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_grounded_chat() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["knowledge_chunks"] > 0

        response = client.post("/api/chat", json={"user_id": "test-user", "text": "Какой рабочий график?"})
        assert response.status_code == 200
        body = response.json()
        assert body["sources"]
        assert "Источник" in body["text"]


def test_unknown_question_requires_hr_confirmation() -> None:
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"user_id": "test-unknown", "text": "Какой цвет выбрать для моего личного автомобиля?"})
        assert response.status_code == 200
        body = response.json()
        assert body["escalated"] is False
        assert body["model_used"] == "none"
        assert body["dialog_state"] == "hr_confirm"
        assert "отправить hr" in body["text"].lower()

        confirmed = client.post("/api/chat", json={"user_id": "test-unknown", "text": "Отправить HR"})
        assert confirmed.status_code == 200
        assert confirmed.json()["escalated"] is True
        assert confirmed.json()["dialog_state"] == "ready"


def test_hr_flow_previews_text_before_sending() -> None:
    with TestClient(app) as client:
        first = client.post("/api/chat", json={"user_id": "test-hr", "text": "/hr"}).json()
        assert first["dialog_state"] == "hr_ask_message"
        preview = client.post("/api/chat", json={"user_id": "test-hr", "text": "Мне не выдали доступ к рабочему порталу."}).json()
        assert preview["dialog_state"] == "hr_confirm"
        assert "Мне не выдали доступ" in preview["text"]
        cancelled = client.post("/api/chat", json={"user_id": "test-hr", "text": "Не сейчас"}).json()
        assert cancelled["escalated"] is False
        assert cancelled["dialog_state"] == "ready"


def test_chat_registration_inside_messenger() -> None:
    with TestClient(app) as client:
        user_id = "test-max-registration"
        first = client.post("/api/chat", json={"user_id": user_id, "text": "/start"})
        assert first.status_code == 200
        assert first.json()["dialog_state"] == "ask_job"
        assert "должность" in first.json()["text"].lower()
        assert "опыт" in client.post("/api/chat", json={"user_id": user_id, "text": "Инженер-технолог"}).json()["text"].lower()
        assert "площадке" in client.post("/api/chat", json={"user_id": user_id, "text": "нет опыта"}).json()["text"].lower()
        assert "первый рабочий день" in client.post("/api/chat", json={"user_id": user_id, "text": "GTP"}).json()["text"].lower()
        start_date = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
        completed = client.post("/api/chat", json={"user_id": user_id, "text": start_date})
        assert completed.status_code == 200
        assert "маршрут готов" in completed.json()["text"].lower()
        assert completed.json()["dialog_state"] == "ask_reminders"
        no_reminders = client.post("/api/chat", json={"user_id": user_id, "text": "не получать"}).json()
        assert no_reminders["dialog_state"] == "ready"
        assert "напоминания отключены" in no_reminders["text"].lower()


def test_webhook_demo_round_trip_stores_chat_id() -> None:
    with TestClient(app) as client:
        response = client.post("/webhooks/max", json={
            "message": {
                "chat_id": "demo-chat", "text": "Что происходит в первый день?",
                "sender": {"user_id": "test-webhook", "name": "Тест"},
            }
        })
        assert response.status_code == 200
        assert response.json()["delivery"]["mode"] == "demo"
        assert app.state.database.get_user("test-webhook")["last_chat_id"] == "demo-chat"
