from __future__ import annotations

import json
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import Database
from app.integrations.max import MaxClient


class ReminderScheduler:
    def __init__(self, database: Database, max_client: MaxClient) -> None:
        self.database = database
        self.max_client = max_client
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    async def deliver_due_reminders(self) -> int:
        delivered = 0
        for reminder in self.database.pending_reminders(datetime.now(timezone.utc).isoformat()):
            user = self.database.get_user(reminder["user_id"])
            if not user:
                self.database.mark_reminder_sent(reminder["id"])
                continue
            payload = json.loads(reminder["payload_json"])
            text = payload.get("text", "У вас есть новое напоминание от Корсика.")
            chat_id = user.get("last_chat_id")
            if not chat_id:
                # Do not guess a MAX recipient from the user id. A reminder can be safely
                # delivered only after an inbound message established the personal chat id.
                self.database.log_delivery("scheduler", user["user_id"], text, {"status": "skipped_missing_chat_id"})
                self.database.mark_reminder_sent(reminder["id"])
                continue
            await self.max_client.send_message(chat_id, text)
            self.database.mark_reminder_sent(reminder["id"])
            delivered += 1
        return delivered

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.add_job(self.deliver_due_reminders, "interval", minutes=1, id="delivery", replace_existing=True)
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
