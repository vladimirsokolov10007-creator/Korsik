from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


WORD_RE = re.compile(r"[a-zа-яё0-9]{3,}", re.IGNORECASE)
# Interrogatives and filler words are not evidence that a source answers a question.
STOPWORDS = {
    "это", "как", "какой", "какая", "какие", "чего", "когда", "где", "почему",
    "можно", "нужно", "хочу", "могу", "мне", "вам", "для", "или", "что",
    "который", "которая", "которые", "будет", "есть", "нет", "про", "могу",
}


@dataclass(frozen=True)
class SourceChunk:
    document: str
    section: str
    text: str
    score: float

    def as_dict(self) -> dict[str, str | float]:
        return {"document": self.document, "section": self.section, "excerpt": self.text, "score": round(self.score, 3)}


class KnowledgeBase:
    """Small transparent RAG retriever for a hackathon MVP.

    It searches approved Markdown/TXT documents only. Replace its scoring layer with an
    embedding/vector store later without changing the bot or GigaChat boundary.
    """

    def __init__(self, knowledge_path: Path) -> None:
        self.knowledge_path = knowledge_path
        self._chunks: list[SourceChunk] = []

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token for token in WORD_RE.findall(text.lower()) if token not in STOPWORDS}

    def reload(self) -> int:
        chunks: list[SourceChunk] = []
        self.knowledge_path.mkdir(parents=True, exist_ok=True)
        for path in sorted([*self.knowledge_path.glob("*.md"), *self.knowledge_path.glob("*.txt")]):
            document = path.stem.replace("_", " ")
            section = "Общее"
            buffer: list[str] = []

            def add_buffer() -> None:
                nonlocal buffer
                paragraph = " ".join(buffer).strip()
                if len(paragraph) >= 40:
                    chunks.append(SourceChunk(document=document, section=section, text=paragraph, score=0.0))
                buffer = []

            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if line.startswith("#"):
                    add_buffer()
                    section = line.lstrip("#").strip() or "Общее"
                elif not line:
                    add_buffer()
                else:
                    buffer.append(line)
            add_buffer()
        self._chunks = chunks
        return len(chunks)

    def search(self, question: str, top_k: int = 3) -> list[SourceChunk]:
        q_tokens = self._tokens(question)
        if not q_tokens:
            return []
        ranked: list[SourceChunk] = []
        for chunk in self._chunks:
            c_tokens = self._tokens(f"{chunk.document} {chunk.section} {chunk.text}")
            overlap = q_tokens & c_tokens
            if not overlap:
                continue
            # overlap ratio + phrase signal: deterministic and inspectable for the demo.
            score = len(overlap) / max(len(q_tokens), 1)
            if overlap:
                score = min(1.0, score + 0.01)
            ranked.append(SourceChunk(chunk.document, chunk.section, chunk.text, score))
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


def grounded_fallback(chunks: list[SourceChunk]) -> str:
    """Returns only retrieved facts when GigaChat is not enabled."""
    best = chunks[0]
    return (
        f"В проверенной базе нашёл следующее: {best.text}\n\n"
        f"Источник: «{best.document}», раздел «{best.section}»."
    )


def build_gigachat_messages(question: str, chunks: list[SourceChunk]) -> list[dict[str, str]]:
    sources = "\n\n".join(
        f"[Источник {index}] Документ: {chunk.document}; раздел: {chunk.section}.\n{chunk.text}"
        for index, chunk in enumerate(chunks, start=1)
    )
    system = (
        "Ты Корсик — AI-наставник по адаптации сотрудников. Отвечай на русском. "
        "Отвечай только на основе источников ниже. Не добавляй фактов, не интерпретируй "
        "нормы как юридическое или кадровое решение и не обещай действий от имени компании. "
        "Если источников недостаточно, прямо скажи об этом. Будь кратким и доброжелательным. "
        "В конце укажи источники формата: Источник: документ — раздел."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Вопрос сотрудника: {question}\n\nПроверенные источники:\n{sources}"},
    ]
