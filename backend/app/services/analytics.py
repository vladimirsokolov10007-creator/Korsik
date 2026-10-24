from __future__ import annotations

from dataclasses import dataclass


TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "доступы и техника": ("доступ", "учётн", "учетн", "парол", "ноутбук", "техника", "vpn"),
    "оформление": ("документ", "оформлен", "договор", "кадры", "справк"),
    "задачи и адаптация": ("не понимаю", "непонят", "задач", "обучен", "адаптац", "ошибк"),
    "обратная связь": ("обратн", "руководител", "встреч", "1:1", "фидбек"),
    "перегрузка": ("перегруз", "устал", "много работ", "не успева", "выгора"),
    "конфликт или напряжение": ("конфликт", "напряж", "обид", "токсич", "давлен"),
}

POSITIVE = ("спасибо", "хорошо", "отлично", "понятно", "нравится", "рад", "удобно")
NEGATIVE = ("плохо", "сложно", "не понимаю", "непонят", "проблем", "конфликт", "устал", "перегруз", "не успева", "тревож")
HIGH_RISK = ("конфликт", "давлен", "дискримин", "домогател", "угроз")


@dataclass(frozen=True)
class FeedbackAnalysis:
    sentiment: str
    topics: list[str]
    risk_level: str


def analyze_feedback(text: str) -> FeedbackAnalysis:
    value = text.lower()
    topics = [topic for topic, keys in TOPIC_KEYWORDS.items() if any(key in value for key in keys)]
    negative_hits = sum(key in value for key in NEGATIVE)
    positive_hits = sum(key in value for key in POSITIVE)
    sentiment = "negative" if negative_hits > positive_hits else "positive" if positive_hits > negative_hits else "neutral"
    risk_level = "high" if any(key in value for key in HIGH_RISK) else "medium" if negative_hits >= 2 else "low"
    return FeedbackAnalysis(sentiment=sentiment, topics=topics or ["без классификации"], risk_level=risk_level)
