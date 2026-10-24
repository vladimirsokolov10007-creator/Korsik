from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.config import Settings
from app.database import Database
from app.integrations.gigachat import GigaChatClient, GigaChatError
from app.services.analytics import analyze_feedback
from app.services.onboarding import employee_route, schedule_onboarding
from app.services.rag import KnowledgeBase, build_gigachat_messages, grounded_fallback


START_COMMANDS = {"/start", "start", "/restart", "/начать"}
HELP_COMMANDS = {"/help", "help", "/помощь"}
HR_COMMANDS = {"/hr", "hr", "/кадры", "обратиться в hr", "передать hr", "нужна помощь hr"}
CANCEL_COMMANDS = {"/cancel", "cancel", "/отмена"}
STATUS_COMMANDS = {"/status", "status", "/статус"}
HR_SEND_COMMANDS = {"/sendhr", "отправить", "отправить hr", "отправить в hr", "да"}
HR_EDIT_COMMANDS = {"изменить", "изменить текст", "редактировать"}
HR_CANCEL_COMMANDS = {"не сейчас", "отмена", "/cancel", "нет"}
LOCATIONS = {
    "grpp": "GrPP",
    "gtp": "GTP",
    "luzhniki": "Luzhniki",
    "не знаю": "Не уточнена",
    "неизвестно": "Не уточнена",
}


class RegistrationInputError(ValueError):
    pass


def parse_start_date(value: str) -> str:
    value = value.strip()
    for pattern in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            parsed = datetime.strptime(value, pattern).date()
            if parsed < date.today():
                raise RegistrationInputError("Эта дата уже прошла. Укажите дату выхода сегодня или позже либо напишите /cancel.")
            return parsed.isoformat()
        except RegistrationInputError:
            raise
        except ValueError:
            continue
    raise RegistrationInputError("Введите дату в формате ДД.ММ.ГГГГ, например 03.11.2026.")


def short_route(user: dict[str, Any]) -> str:
    return "\n".join(f"• {item['title']}: {item['detail']}" for item in employee_route(user))


def welcome_text() -> str:
    return (
        "Здравствуйте! Я Корсик, помощник по адаптации. Помогу собрать маршрут на первые недели "
        "и найти информацию в утверждённых документах.\n\n"
        "Не отправляйте в чат пароли, паспортные данные, сведения о здоровье и другую чувствительную информацию. "
        "Я передаю обращение HR только после вашего подтверждения.\n\n"
        "Я задам четыре коротких вопроса. Опрос можно остановить в любой момент: /cancel.\n\n"
        "Какая у вас должность? Это нужно, чтобы подобрать полезные первые шаги."
    )


def help_text() -> str:
    return (
        "Я помогаю с адаптацией и отвечаю только по утверждённым документам.\n"
        "Команды: /start — собрать или обновить маршрут; /status — показать маршрут; "
        "/hr — подготовить обращение HR; /cancel — остановить опрос и отменить будущие напоминания.\n\n"
        "Если в базе знаний нет ответа, я не буду гадать и предложу подготовить обращение HR. "
        "Передача текста происходит только после вашего подтверждения."
    )


@dataclass(frozen=True)
class ChatResult:
    text: str
    sources: list[dict[str, Any]]
    escalated: bool
    model_used: str
    dialog_state: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "sources": self.sources,
            "escalated": self.escalated,
            "model_used": self.model_used,
            "dialog_state": self.dialog_state,
        }


class KorsikChatService:
    def __init__(self, settings: Settings, database: Database, knowledge_base: KnowledgeBase, gigachat: GigaChatClient) -> None:
        self.settings = settings
        self.database = database
        self.knowledge_base = knowledge_base
        self.gigachat = gigachat

    def _finish(
        self,
        user_id: str,
        text: str,
        *,
        sources: list[dict[str, Any]] | None = None,
        escalated: bool = False,
        model_used: str = "none",
    ) -> ChatResult:
        self.database.save_message(user_id, "out", text, sources)
        user = self.database.get_user(user_id) or {}
        return ChatResult(
            text=text,
            sources=sources or [],
            escalated=escalated,
            model_used=model_used,
            dialog_state=user.get("dialog_state", "ready"),
        )

    def _start_registration(self, user_id: str) -> ChatResult:
        self.database.delete_pending_reminders(user_id)
        self.database.update_employee_fields(
            user_id,
            onboarding_stage="registration",
            dialog_state="ask_job",
            pending_hr_text="",
        )
        return self._finish(user_id, welcome_text())

    def _start_hr_request(self, user_id: str) -> ChatResult:
        self.database.update_employee_fields(user_id, dialog_state="hr_ask_message", pending_hr_text="")
        return self._finish(
            user_id,
            "Опишите вопрос одним сообщением. Перед отправкой я покажу текст обращения и попрошу подтвердить передачу HR.",
        )

    def _offer_hr(self, user_id: str, text: str, intro: str) -> ChatResult:
        self.database.update_employee_fields(user_id, dialog_state="hr_confirm", pending_hr_text=text)
        return self._finish(
            user_id,
            f"{intro}\n\n"
            f"Могу подготовить обращение HR с вашим текстом:\n«{text}»\n\n"
            "Напишите «Отправить HR», чтобы подтвердить передачу, «Изменить текст» или «Не сейчас».",
        )

    def _handle_hr_dialog(self, user: dict[str, Any], text: str) -> ChatResult | None:
        state = user.get("dialog_state", "ready")
        user_id = user["user_id"]
        normalised = text.lower().strip()

        if state == "hr_ask_message":
            if len(text.strip()) < 5:
                return self._finish(user_id, "Опишите вопрос немного подробнее, чтобы HR мог помочь. Или напишите /cancel.")
            return self._offer_hr(user_id, text.strip(), "Проверьте текст обращения.")

        if state == "hr_confirm":
            if normalised in HR_SEND_COMMANDS:
                message = user.get("pending_hr_text", "").strip()
                if not message:
                    return self._start_hr_request(user_id)
                escalation_id = self.database.create_escalation(user_id, "Обращение подтверждено сотрудником", message)
                self.database.update_employee_fields(user_id, dialog_state="ready", pending_hr_text="")
                return self._finish(
                    user_id,
                    "Обращение зарегистрировано в очереди HR. Я не могу подтвердить срок ответа. "
                    "Если ситуация срочная, воспользуйтесь утверждённым каналом связи с HR или обратитесь к руководителю.",
                    escalated=True,
                )
            if normalised in HR_EDIT_COMMANDS:
                self.database.update_employee_fields(user_id, dialog_state="hr_ask_message", pending_hr_text="")
                return self._finish(user_id, "Напишите новую версию обращения. Перед отправкой я снова покажу её для подтверждения.")
            if normalised in HR_CANCEL_COMMANDS:
                self.database.update_employee_fields(user_id, dialog_state="ready", pending_hr_text="")
                return self._finish(user_id, "Хорошо, обращение не отправлено. Вы можете вернуться к этому позже командой /hr.")
            return self._finish(user_id, "Чтобы подтвердить передачу, напишите «Отправить HR». Также можно написать «Изменить текст» или «Не сейчас».")

        return None

    def _handle_registration(self, user: dict[str, Any], text: str) -> ChatResult | None:
        state = user.get("dialog_state", "ready")
        user_id = user["user_id"]
        if state == "ready":
            return None
        if state == "ask_job":
            if len(text.strip()) < 2:
                return self._finish(user_id, "Напишите должность полностью, например: «инженер-технолог».")
            self.database.update_employee_fields(user_id, job_title=text.strip(), dialog_state="ask_experience")
            return self._finish(
                user_id,
                "Спасибо. Есть ли у вас опыт на похожей должности? Это нужно только для уровня подсказок, а не для оценки. "
                "Напишите «есть опыт» или «нет опыта».",
            )
        if state == "ask_experience":
            normalised = text.lower().strip()
            if "нович" in normalised or normalised in {"нет", "нет опыта"}:
                experience = "new"
            elif "опыт" in normalised or normalised in {"да", "есть", "есть опыт"}:
                experience = "experienced"
            else:
                return self._finish(user_id, "Не удалось определить вариант. Напишите «есть опыт» или «нет опыта».")
            self.database.update_employee_fields(user_id, experience_level=experience, dialog_state="ask_location")
            return self._finish(
                user_id,
                "На какой площадке вы будете работать? Выберите: GrPP, GTP или Luzhniki. Если пока не знаете, напишите «не знаю».",
            )
        if state == "ask_location":
            location = LOCATIONS.get(text.lower().strip())
            if not location:
                return self._finish(user_id, "Выберите GrPP, GTP или Luzhniki. Если площадка пока неизвестна, напишите «не знаю».")
            self.database.update_employee_fields(user_id, location=location, dialog_state="ask_start_date")
            return self._finish(user_id, "Когда ваш первый рабочий день? Введите дату в формате ДД.ММ.ГГГГ, например 03.11.2026.")
        if state == "ask_start_date":
            try:
                start_date = parse_start_date(text)
            except RegistrationInputError as error:
                return self._finish(user_id, str(error))
            self.database.delete_pending_reminders(user_id)
            self.database.update_employee_fields(
                user_id,
                start_date=start_date,
                onboarding_stage="route_ready",
                dialog_state="ask_reminders",
            )
            updated = self.database.get_user(user_id) or user
            return self._finish(
                user_id,
                "Маршрут готов.\n\n"
                + short_route(updated)
                + "\n\nХотите получать короткие напоминания о ходе адаптации примерно в 18:30 по московскому времени? "
                "Напишите «получать» или «не получать».",
            )
        if state == "ask_reminders":
            normalised = text.lower().strip()
            if normalised in {"получать", "да", "хочу", "включить"}:
                self.database.update_employee_fields(user_id, consent_to_pulse=True, dialog_state="ready")
                updated = self.database.get_user(user_id) or user
                schedule_onboarding(self.database, updated, self.settings.onboarding_timezone)
                return self._finish(
                    user_id,
                    "Напоминания включены. Я напишу накануне выхода, в первый рабочий день, через несколько дней и через две недели. "
                    "Отключить будущие напоминания можно командой /cancel.",
                )
            if normalised in {"не получать", "нет", "не хочу", "выключить"}:
                self.database.delete_pending_reminders(user_id)
                self.database.update_employee_fields(user_id, consent_to_pulse=False, dialog_state="ready")
                return self._finish(
                    user_id,
                    "Хорошо, напоминания отключены. Маршрут сохранён; его можно открыть в любой момент командой /status.",
                )
            return self._finish(user_id, "Напишите «получать», чтобы включить напоминания, или «не получать», чтобы продолжить без них.")
        self.database.set_dialog_state(user_id, "ready")
        return None

    async def reply(self, user_id: str, question: str) -> ChatResult:
        user = self.database.ensure_employee(user_id)
        self.database.save_message(user_id, "in", question)
        normalised = question.lower().strip()

        if normalised in START_COMMANDS:
            return self._start_registration(user_id)
        if normalised in HELP_COMMANDS:
            return self._finish(user_id, help_text())
        if normalised in CANCEL_COMMANDS:
            self.database.delete_pending_reminders(user_id)
            self.database.update_employee_fields(
                user_id,
                onboarding_stage="registered",
                dialog_state="ready",
                pending_hr_text="",
                consent_to_pulse=False,
            )
            return self._finish(user_id, "Опрос остановлен, будущие напоминания отменены. Когда будете готовы начать заново, напишите /start.")
        if normalised in HR_COMMANDS:
            return self._start_hr_request(user_id)
        if normalised in STATUS_COMMANDS:
            current = self.database.get_user(user_id) or user
            if current.get("onboarding_stage") != "route_ready":
                return self._finish(user_id, "Персональный маршрут ещё не собран. Напишите /start, и я задам четыре коротких вопроса.")
            return self._finish(user_id, "Ваш маршрут адаптации:\n\n" + short_route(current))

        user = self.database.get_user(user_id) or user
        hr_reply = self._handle_hr_dialog(user, question)
        if hr_reply:
            return hr_reply
        registration_reply = self._handle_registration(user, question)
        if registration_reply:
            return registration_reply

        feedback = analyze_feedback(question)
        if feedback.sentiment == "negative" or feedback.risk_level in {"medium", "high"}:
            self.database.save_feedback(user_id, "free_text", question, feedback.sentiment, feedback.topics, feedback.risk_level)

        chunks = self.knowledge_base.search(question)
        sources = [chunk.as_dict() for chunk in chunks]
        if not chunks or chunks[0].score < self.settings.rag_min_score:
            return self._offer_hr(
                user_id,
                question,
                "В утверждённых документах нет ответа на этот вопрос. Я не буду гадать.",
            )

        model_used = "retrieval_only"
        if not self.settings.demo_mode and self.gigachat.configured:
            try:
                text = await self.gigachat.answer(build_gigachat_messages(question, chunks))
                model_used = "gigachat"
            except GigaChatError:
                text = grounded_fallback(chunks) + "\n\nСейчас могу привести только выдержку из утверждённого документа."
        else:
            text = grounded_fallback(chunks)

        if feedback.risk_level == "high":
            self.database.update_employee_fields(user_id, dialog_state="hr_confirm", pending_hr_text=question)
            text += (
                "\n\nПохоже, ситуация может требовать личной поддержки. Ваше сообщение пока никуда не отправлено. "
                "Хотите передать его HR? Напишите «Отправить HR», «Изменить текст» или «Не сейчас»."
            )
        return self._finish(user_id, text, sources=sources, model_used=model_used)
