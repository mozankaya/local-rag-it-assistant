from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.n8n_client import N8nClientError, post_to_n8n


router = APIRouter(tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(
    request: FeedbackRequest,
    settings: Settings = Depends(get_settings),
) -> FeedbackResponse:
    payload = request.model_dump()

    try:
        n8n_response = await post_to_n8n(
            url=settings.n8n_feedback_webhook_url,
            payload=payload,
            timeout_seconds=settings.request_timeout_seconds,
        )

    except N8nClientError:
        raise HTTPException(
            status_code=502,
            detail="Geri bildirim servisine şu anda ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
        )

    return FeedbackResponse(
        status=str(n8n_response.get("status", "success")),
        message=n8n_response.get("message"),
        feedback=n8n_response.get("feedback", request.feedback),
    )