from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR.parent / ".env")


def as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    demo_mode: bool
    database_path: Path
    knowledge_base_path: Path
    rag_min_score: float
    dashboard_admin_token: str
    gigachat_authorization_key: str
    gigachat_scope: str
    gigachat_model: str
    gigachat_verify_ssl: bool
    gigachat_ca_bundle: str
    max_bot_token: str
    max_send_message_url: str
    max_recipient_location: str
    max_recipient_field: str
    max_webhook_secret: str
    max_webhook_secret_header: str
    max_auth_header: str
    max_auth_value_template: str
    max_send_interactive_buttons: bool
    onboarding_timezone: str

    @classmethod
    def from_env(cls) -> "Settings":
        def resolve_path(value: str, fallback: Path) -> Path:
            candidate = Path(value) if value else fallback
            return candidate if candidate.is_absolute() else BASE_DIR / candidate

        return cls(
            app_name=os.getenv("APP_NAME", "Korsik 2.0"),
            demo_mode=as_bool(os.getenv("DEMO_MODE"), True),
            database_path=resolve_path(os.getenv("DATABASE_PATH", "data/korsik.db"), BASE_DIR / "data/korsik.db"),
            knowledge_base_path=resolve_path(os.getenv("KNOWLEDGE_BASE_PATH", "data/knowledge_base"), BASE_DIR / "data/knowledge_base"),
            rag_min_score=float(os.getenv("RAG_MIN_SCORE", "0.18")),
            dashboard_admin_token=os.getenv("DASHBOARD_ADMIN_TOKEN", ""),
            gigachat_authorization_key=os.getenv("GIGACHAT_AUTHORIZATION_KEY", "").strip(),
            gigachat_scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
            gigachat_model=os.getenv("GIGACHAT_MODEL", "GigaChat"),
            gigachat_verify_ssl=as_bool(os.getenv("GIGACHAT_VERIFY_SSL"), True),
            gigachat_ca_bundle=os.getenv("GIGACHAT_CA_BUNDLE", "").strip(),
            max_bot_token=os.getenv("MAX_BOT_TOKEN", "").strip(),
            max_send_message_url=os.getenv("MAX_SEND_MESSAGE_URL", "").strip(),
            max_recipient_location=os.getenv("MAX_RECIPIENT_LOCATION", "body").strip().lower(),
            max_recipient_field=os.getenv("MAX_RECIPIENT_FIELD", "chat_id").strip(),
            max_webhook_secret=os.getenv("MAX_WEBHOOK_SECRET", "").strip(),
            max_webhook_secret_header=os.getenv("MAX_WEBHOOK_SECRET_HEADER", "X-Max-Webhook-Secret").strip(),
            max_auth_header=os.getenv("MAX_AUTH_HEADER", "Authorization"),
            max_auth_value_template=os.getenv("MAX_AUTH_VALUE_TEMPLATE", "Bearer {token}"),
            max_send_interactive_buttons=as_bool(os.getenv("MAX_SEND_INTERACTIVE_BUTTONS"), False),
            onboarding_timezone=os.getenv("ONBOARDING_TIMEZONE", "Europe/Moscow"),
        )


settings = Settings.from_env()
