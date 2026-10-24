from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(tags=["system"])


def require_admin(request: Request, x_dashboard_token: str | None) -> None:
    settings = request.app.state.settings
    if settings.demo_mode:
        return
    if not settings.dashboard_admin_token or x_dashboard_token != settings.dashboard_admin_token:
        raise HTTPException(status_code=401, detail="Требуется авторизация администратора")


@router.get("/api/health")
async def health(request: Request) -> dict:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "mode": "demo" if settings.demo_mode else "integration",
        "knowledge_chunks": request.app.state.knowledge_base.chunk_count,
        "gigachat_configured": bool(settings.gigachat_authorization_key),
        "max_configured": request.app.state.max_client.configured,
    }


@router.post("/api/admin/reload-knowledge")
async def reload_knowledge(request: Request, x_dashboard_token: str | None = Header(default=None)) -> dict:
    require_admin(request, x_dashboard_token)
    count = request.app.state.knowledge_base.reload()
    return {"reloaded": count}


@router.post("/api/admin/run-reminders")
async def run_reminders(request: Request, x_dashboard_token: str | None = Header(default=None)) -> dict:
    require_admin(request, x_dashboard_token)
    delivered = await request.app.state.reminder_scheduler.deliver_due_reminders()
    return {"delivered": delivered}
