from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["employee", "hr", "manager", "director"]


class EmployeeProfileIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=100)
    job_title: str = Field(default="Новый сотрудник", max_length=120)
    manager_name: str = Field(default="Руководитель не указан", max_length=100)
    location: str = Field(default="Не указана", max_length=100)
    start_date: date | None = None
    experience_level: Literal["new", "experienced"] = "new"
    preferred_hours: str = Field(default="18:30–20:00", max_length=50)
    career_goal: str = Field(default="", max_length=500)
    consent_to_pulse: bool = True


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=2000)
    chat_id: str | None = Field(default=None, max_length=100)


class FeedbackIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=2000)
    stage: str = Field(default="pulse", max_length=80)


class EscalationIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=2000)
    source_message: str = Field(default="", max_length=2000)


class MaxUpdate(BaseModel):
    """Deliberately permissive envelope: MAX update schemas differ by bot API version."""
    model_config = {"extra": "allow"}
