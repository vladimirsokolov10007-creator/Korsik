from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import ChatRequest, EmployeeProfileIn, EscalationIn, FeedbackIn
from app.services.analytics import analyze_feedback
from app.services.onboarding import employee_route, schedule_onboarding

router = APIRouter(prefix="/api", tags=["employee"])


@router.post("/onboarding/profile")
async def save_profile(payload: EmployeeProfileIn, request: Request) -> dict:
    database = request.app.state.database
    user = database.upsert_user(payload.model_dump(mode="json"))
    database.delete_pending_reminders(payload.user_id)
    schedule_onboarding(database, user, request.app.state.settings.onboarding_timezone)
    database.update_employee_fields(payload.user_id, onboarding_stage="route_ready", dialog_state="ready")
    user = database.get_user(payload.user_id) or user
    return {"user": user, "route": employee_route(user)}


@router.get("/onboarding/{user_id}")
async def onboarding_route(user_id: str, request: Request) -> dict:
    database = request.app.state.database
    user = database.get_user(user_id) or database.ensure_employee(user_id)
    return {"user": user, "route": employee_route(user)}


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request) -> dict:
    if payload.chat_id:
        request.app.state.database.ensure_employee(payload.user_id)
        request.app.state.database.update_employee_fields(payload.user_id, last_chat_id=payload.chat_id)
    result = await request.app.state.chat_service.reply(payload.user_id, payload.text)
    return result.as_dict()


@router.post("/feedback")
async def create_feedback(payload: FeedbackIn, request: Request) -> dict:
    database = request.app.state.database
    database.ensure_employee(payload.user_id)
    analysis = analyze_feedback(payload.text)
    database.save_feedback(payload.user_id, payload.stage, payload.text, analysis.sentiment, analysis.topics, analysis.risk_level)
    # Feedback is analysed for the aggregate demo. It is never forwarded to HR without
    # explicit confirmation from the employee in the chat scenario.
    return {"analysis": analysis.__dict__, "escalation_id": None}


@router.post("/escalations")
async def create_escalation(payload: EscalationIn, request: Request) -> dict:
    database = request.app.state.database
    database.ensure_employee(payload.user_id)
    escalation_id = database.create_escalation(payload.user_id, payload.reason, payload.source_message)
    return {"id": escalation_id, "status": "open", "message": "Обращение передано HR-менеджеру."}
