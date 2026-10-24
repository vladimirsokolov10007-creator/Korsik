from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/api/dashboard", tags=["dashboards"])


def require_dashboard_access(request: Request, x_dashboard_token: str | None = Header(default=None)) -> None:
    settings = request.app.state.settings
    if settings.demo_mode:
        return
    if not settings.dashboard_admin_token or x_dashboard_token != settings.dashboard_admin_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация дашборда")


@router.get("/hr", dependencies=[])
async def hr_dashboard(request: Request, x_dashboard_token: str | None = Header(default=None)) -> dict:
    require_dashboard_access(request, x_dashboard_token)
    database = request.app.state.database
    return {"summary": database.dashboard_summary(), "escalations": database.list_open_escalations(), "analytics": database.analytics()}


@router.post("/hr/escalations/{escalation_id}/resolve")
async def resolve_escalation(escalation_id: int, request: Request, x_dashboard_token: str | None = Header(default=None)) -> dict:
    require_dashboard_access(request, x_dashboard_token)
    if not request.app.state.database.resolve_escalation(escalation_id):
        raise HTTPException(status_code=404, detail="Открытое обращение не найдено")
    return {"id": escalation_id, "status": "resolved"}


@router.get("/manager")
async def manager_dashboard(request: Request, manager_name: str | None = None, x_dashboard_token: str | None = Header(default=None)) -> dict:
    require_dashboard_access(request, x_dashboard_token)
    team = request.app.state.database.manager_team(manager_name)
    return {
        "team": team,
        "meeting_prompt": "Запланируйте личную встречу с каждым новым сотрудником в первую неделю и зафиксируйте договорённости в утверждённой HR-системе.",
    }


@router.get("/director")
async def director_dashboard(request: Request, x_dashboard_token: str | None = Header(default=None)) -> dict:
    require_dashboard_access(request, x_dashboard_token)
    period_start = datetime.now(timezone.utc) - timedelta(days=7)
    analytics = request.app.state.database.analytics(since=period_start)
    topics = sorted(analytics["topics"].items(), key=lambda item: item[1], reverse=True)
    return {
        "weekly_digest": {
            "sample_size": analytics["sample_size"],
            "sentiment": analytics["sentiment"],
            "risk_feedback": analytics["risk_feedback"],
            "top_topics": [{"topic": topic, "count": count} for topic, count in topics[:5]],
            "period_start": period_start.date().isoformat(),
            "period_end": datetime.now(timezone.utc).date().isoformat(),
        },
        "note": "Сводка охватывает последние 7 дней и содержит только агрегированные данные. Не используйте её как основание для кадровых решений о конкретном сотруднике.",
    }
