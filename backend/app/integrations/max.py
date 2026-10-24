from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.database import Database


class MaxConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class IncomingMessage:
    user_id: str
    chat_id: str
    text: str
    display_name: str


def _first(mapping: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = mapping.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return default


def parse_max_update(payload: dict[str, Any]) -> IncomingMessage | None:
    """Normalises common MAX update envelopes.

    The transport shell is intentionally isolated because final fields must be verified
    against the MAX developer documentation enabled for the created bot account.
    """
    message = payload.get("message") or payload.get("update", {}).get("message") or payload
    if not isinstance(message, dict):
        return None
    body = message.get("body") if isinstance(message.get("body"), dict) else {}
    sender = message.get("sender") if isinstance(message.get("sender"), dict) else {}
    recipient = message.get("recipient") if isinstance(message.get("recipient"), dict) else {}
    text = _first(body, "text", "message") or _first(message, "text")
    chat_id = (
        _first(recipient, "chat_id", "chatId", "id")
        or _first(message, "chat_id", "chatId", "recipient_id", "recipientId")
    )
    user_id = _first(sender, "user_id", "userId", "id") or _first(message, "user_id", "userId", "sender_id")
    name = _first(sender, "name", "display_name", "displayName", default="Коллега")
    if not text.strip() or not user_id or not chat_id:
        return None
    return IncomingMessage(user_id=user_id, chat_id=chat_id, text=text.strip(), display_name=name)


class MaxClient:
    """Outbound MAX adapter. No credentials ever enter browser code."""

    def __init__(self, settings: Settings, database: Database, http_client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.database = database
        self.http = http_client

    @property
    def configured(self) -> bool:
        return bool(self.settings.max_bot_token and self.settings.max_send_message_url)

    async def send_message(self, chat_id: str, text: str, buttons: list[dict[str, str]] | None = None) -> dict[str, Any]:
        """Sends a plain-text message through the exact transport selected in .env.

        MAX API versions may put the recipient in a JSON body, query string or URL. The
        business logic never needs to change for that: set MAX_RECIPIENT_LOCATION and
        MAX_RECIPIENT_FIELD after checking the developer-cabinet reference.
        """
        payload: dict[str, Any] = {"text": text}
        if buttons and self.settings.max_send_interactive_buttons:
            # Enable only after validating the buttons schema against the active MAX API.
            payload["buttons"] = buttons
        url = self.settings.max_send_message_url
        params: dict[str, str] | None = None
        location = self.settings.max_recipient_location
        field = self.settings.max_recipient_field
        if location == "body":
            payload[field] = chat_id
        elif location == "query":
            params = {field: chat_id}
        elif location == "url_template":
            if "{chat_id}" not in url:
                raise MaxConfigurationError("Для MAX_RECIPIENT_LOCATION=url_template добавьте {chat_id} в MAX_SEND_MESSAGE_URL")
            url = url.replace("{chat_id}", chat_id)
        else:
            raise MaxConfigurationError("MAX_RECIPIENT_LOCATION должен быть body, query или url_template")
        log_payload = {"url": url, "params": params, "body": payload}
        if self.settings.demo_mode:
            self.database.log_delivery("mock-max", chat_id, text, log_payload)
            return {"mode": "demo", "delivered": True, "payload": log_payload}
        if not self.configured:
            raise MaxConfigurationError("MAX не настроен: заполните MAX_BOT_TOKEN и MAX_SEND_MESSAGE_URL в .env")
        headers = {
            self.settings.max_auth_header: self.settings.max_auth_value_template.format(token=self.settings.max_bot_token),
            "Accept": "application/json",
        }
        response = await self.http.post(url, headers=headers, params=params, json=payload)
        if response.is_error:
            raise MaxConfigurationError(f"MAX не принял сообщение: HTTP {response.status_code}")
        self.database.log_delivery("max", chat_id, text, log_payload)
        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "delivered": True}
