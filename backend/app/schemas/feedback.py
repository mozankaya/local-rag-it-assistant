from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.chat import Source


class FeedbackRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    feedback: Literal["useful", "not_useful"]
    sources: list[Source] = []

    @field_validator("question", "answer")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Alan boş olamaz.")

        return cleaned


class FeedbackResponse(BaseModel):
    status: str
    message: str | None = None
    feedback: str | None = None