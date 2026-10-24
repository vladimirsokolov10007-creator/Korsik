from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Database
from app.integrations.gigachat import GigaChatClient
from app.integrations.max import MaxClient
from app.routers import chat, dashboard, max_demo, system, webhook
from app.services.chat import KorsikChatService
from app.services.rag import KnowledgeBase
from app.services.scheduler import ReminderScheduler

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    database = Database(settings.database_path)
    database.initialize()
    knowledge_base = KnowledgeBase(settings.knowledge_base_path)
    knowledge_base.reload()
    verify: bool | str = settings.gigachat_verify_ssl
    if settings.gigachat_ca_bundle:
        verify = settings.gigachat_ca_bundle
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0), verify=verify)
    max_client = MaxClient(settings, database, http_client)
    reminder_scheduler = ReminderScheduler(database, max_client)
    app.state.settings = settings
    app.state.database = database
    app.state.knowledge_base = knowledge_base
    app.state.gigachat_client = GigaChatClient(settings, http_client)
    app.state.max_client = max_client
    app.state.chat_service = KorsikChatService(settings, database, knowledge_base, app.state.gigachat_client)
    app.state.reminder_scheduler = reminder_scheduler
    reminder_scheduler.start()
    try:
        yield
    finally:
        reminder_scheduler.shutdown()
        await http_client.aclose()


app = FastAPI(
    title="Korsik 2.0",
    description="AI-наставник по адаптации сотрудников: MAX + RAG + GigaChat",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(system.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(webhook.router)
app.include_router(max_demo.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
