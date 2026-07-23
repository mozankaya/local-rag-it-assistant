from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_questions: int
    today_questions: int
    total_feedback: int
    useful_feedback: int
    not_useful_feedback: int
    no_relevant_source_count: int
    out_of_scope_count: int
    llm_error_count: int
    total_users: int
    admin_users: int
    standard_users: int


class ResponseTypeCount(BaseModel):
    response_type: str
    count: int


class CategoryCount(BaseModel):
    category: str
    count: int


class FeedbackSummaryResponse(BaseModel):
    total_feedback: int
    useful_feedback: int
    not_useful_feedback: int


class RecentQuestionResponse(BaseModel):
    id: int
    question: str
    answer_preview: Optional[str] = None
    category: Optional[str] = None
    section_title: Optional[str] = None
    response_type: Optional[str] = None
    created_at: Optional[datetime] = None


class PaginatedRecentQuestionsResponse(BaseModel):
    items: list[RecentQuestionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
    
    
class ReviewItemResponse(BaseModel):
    item_type: str
    item_id: int
    review_reason: str
    question: str
    answer_preview: Optional[str] = None
    feedback: Optional[str] = None
    response_type: Optional[str] = None
    category: Optional[str] = None
    section_title: Optional[str] = None
    created_at: Optional[datetime] = None


class PaginatedReviewItemsResponse(BaseModel):
    items: list[ReviewItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool