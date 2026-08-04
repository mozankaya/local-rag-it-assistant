from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.api.routes.auth import get_current_user
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.feedback import (
    FeedbackRequest,
    FeedbackResponse,
)
from app.services.n8n_client import (
    N8nClientError,
    post_to_n8n,
)

router = APIRouter(tags=["Feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
)
async def feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> FeedbackResponse:
    """Forward feedback to n8n and reject missing, unsuccessful, or malformed chat records."""

    payload = request.model_dump()

    try:
        n8n_response = await post_to_n8n(
            url=settings.n8n_feedback_webhook_url,
            payload=payload,
            timeout_seconds=(settings.request_timeout_seconds),
            webhook_secret=settings.n8n_webhook_secret,
        )

    except N8nClientError:
        raise HTTPException(
            status_code=502,
            detail=(
                "Geri bildirim servisine şu anda "
                "ulaşılamıyor. Lütfen daha sonra "
                "tekrar deneyin."
            ),
        )

    status = str(n8n_response.get("status", "error"))

    if status == "not_found":
        raise HTTPException(
            status_code=404,
            detail=("Geri bildirim gönderilecek " "sohbet kaydı bulunamadı."),
        )

    if status != "success":
        raise HTTPException(
            status_code=502,
            detail=("Geri bildirim servisinden " "geçerli bir sonuç alınamadı."),
        )

    chat_log_id_value = n8n_response.get(
        "chat_log_id",
        request.chat_log_id,
    )

    if isinstance(chat_log_id_value, bool):
        raise HTTPException(
            status_code=502,
            detail=(
                "Geri bildirim servisinden geçerli " "bir sohbet kimliği alınamadı."
            ),
        )

    try:
        chat_log_id = int(chat_log_id_value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail=(
                "Geri bildirim servisinden geçerli " "bir sohbet kimliği alınamadı."
            ),
        )

    if chat_log_id <= 0:
        raise HTTPException(
            status_code=502,
            detail=(
                "Geri bildirim servisinden geçerli " "bir sohbet kimliği alınamadı."
            ),
        )

    return FeedbackResponse(
        status=status,
        message=n8n_response.get("message"),
        feedback=n8n_response.get(
            "feedback",
            request.feedback,
        ),
        chat_log_id=chat_log_id,
    )
