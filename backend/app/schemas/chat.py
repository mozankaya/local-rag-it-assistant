from typing import Any

from pydantic import BaseModel, Field, field_validator


class Source(BaseModel):
    document_id: str | None = None
    title: str | None = None
    category: str | None = None
    section_title: str | None = None
    chunk_index: int | str | None = None
    source_file_name: str | None = None
    file_type: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Soru boş olamaz.")

        return cleaned


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source] = []


class N8nChatResponse(BaseModel):
    question: str | None = None
    answer: str | None = None
    sources: list[dict[str, Any]] = []