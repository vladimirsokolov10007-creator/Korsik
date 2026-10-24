from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import httpx

from app.config import Settings

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class GigaChatError(RuntimeError):
    pass


class GigaChatClient:
    """Server-side GigaChat REST client with a cached OAuth access token."""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.http = http_client
        self._access_token: str | None = None
        self._expires_at = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        return bool(self.settings.gigachat_authorization_key)

    async def _get_access_token(self, force_refresh: bool = False) -> str:
        if not self.configured:
            raise GigaChatError("GigaChat не настроен: добавьте GIGACHAT_AUTHORIZATION_KEY в .env")
        if not force_refresh and self._access_token and time.time() < self._expires_at - 60:
            return self._access_token

        async with self._token_lock:
            if not force_refresh and self._access_token and time.time() < self._expires_at - 60:
                return self._access_token
            response = await self.http.post(
                OAUTH_URL,
                headers={
                    # Authorization data is supplied by the GigaChat console. Do not encode it again.
                    "Authorization": f"Basic {self.settings.gigachat_authorization_key}",
                    "RqUID": str(uuid.uuid4()),
                    "Accept": "application/json",
                },
                data={"scope": self.settings.gigachat_scope},
            )
            if response.is_error:
                raise GigaChatError(f"Не удалось получить токен GigaChat: HTTP {response.status_code}")
            payload = response.json()
            try:
                self._access_token = payload["access_token"]
                self._expires_at = float(payload["expires_at"]) / 1000
            except (KeyError, TypeError, ValueError) as error:
                raise GigaChatError("GigaChat вернул неполный OAuth-ответ") from error
            return self._access_token

    async def answer(self, messages: list[dict[str, str]]) -> str:
        """Makes no model request in demo mode; caller decides when this is allowed."""
        async def request_once(token: str) -> httpx.Response:
            return await self.http.post(
                CHAT_URL,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                json={
                    "model": self.settings.gigachat_model,
                    "messages": messages,
                    "temperature": 0.15,
                    "max_tokens": 500,
                    "stream": False,
                },
            )

        token = await self._get_access_token()
        response = await request_once(token)
        if response.status_code == 401:
            self._access_token = None
            token = await self._get_access_token(force_refresh=True)
            response = await request_once(token)
        if response.is_error:
            raise GigaChatError(f"GigaChat не ответил: HTTP {response.status_code}")
        try:
            content: Any = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise GigaChatError("Неожиданный формат ответа GigaChat") from error
        if not isinstance(content, str) or not content.strip():
            raise GigaChatError("GigaChat вернул пустой ответ")
        return content.strip()
