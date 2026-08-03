from typing import Literal

from pydantic import BaseModel, Field

FeedbackValue = Literal[
    "useful",
    "not_useful",
]


class FeedbackRequest(BaseModel):
    chat_log_id: int = Field(..., gt=0)
    feedback: FeedbackValue


class FeedbackResponse(BaseModel):
    status: str
    message: str | None = None
    feedback: FeedbackValue | None = None
    chat_log_id: int | None = None
