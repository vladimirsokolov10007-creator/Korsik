from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.integrations.max import MaxConfigurationError, parse_max_update

router = APIRouter(prefix="/webhooks", tags=["MAX"])


@router.post("/max")
async def max_webhook(request: Request) -> dict:
    """Receives a MAX bot update and returns a safe, fast acknowledgement.

    The deployment uses the verification header selected in .env. Match its name and
    signature scheme to the current MAX developer-cabinet documentation before enabling
    integration mode; never expose a public, unsigned production webhook.
    """
    settings = request.app.state.settings
    received_secret = request.headers.get(settings.max_webhook_secret_header)
    if not settings.demo_mode and not settings.max_webhook_secret:
        raise HTTPException(status_code=503, detail="В integration mode требуется MAX_WEBHOOK_SECRET")
    if settings.max_webhook_secret and received_secret != settings.max_webhook_secret:
        raise HTTPException(status_code=401, detail="Неверный webhook secret")
    try:
        payload = await request.json()
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Ожидается JSON") from error
    incoming = parse_max_update(payload)
    if incoming is None:
        return {"accepted": True, "ignored": True, "reason": "Не найдено текстовое сообщение"}

    database = request.app.state.database
    database.ensure_employee(incoming.user_id, incoming.display_name)
    database.update_employee_fields(incoming.user_id, last_chat_id=incoming.chat_id)
    result = await request.app.state.chat_service.reply(incoming.user_id, incoming.text)
    try:
        # Interactive button schema is deliberately not guessed. The approved MAX button
        # payloads can be added in the adapter after the partner-cabinet API is available.
        delivery = await request.app.state.max_client.send_message(incoming.chat_id, result.text)
    except MaxConfigurationError as error:
        # This should alert the operator while preserving a valid acknowledgement format.
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"accepted": True, "reply": result.as_dict(), "delivery": delivery}
