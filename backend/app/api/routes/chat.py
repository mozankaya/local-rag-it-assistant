from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request as HttpRequest,
)

from app.api.routes.auth import get_current_user
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.n8n_client import (
    N8nClientError,
    post_to_n8n,
)

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: HttpRequest,
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    if len(request.question) > settings.max_question_length:
        raise HTTPException(
            status_code=400,
            detail=("Soru çok uzun. " "Lütfen daha kısa bir soru girin."),
        )

    request_id = getattr(
        http_request.state,
        "request_id",
        None,
    )

    payload = {
        "question": request.question,
    }

    if request_id:
        payload["request_id"] = request_id

    try:
        n8n_response = await post_to_n8n(
            url=settings.n8n_rag_webhook_url,
            payload=payload,
            timeout_seconds=(settings.request_timeout_seconds),
            webhook_secret=settings.n8n_webhook_secret,
        )

    except N8nClientError:
        raise HTTPException(
            status_code=502,
            detail=(
                "Chatbot servisine şu anda ulaşılamıyor. "
                "Lütfen daha sonra tekrar deneyin."
            ),
        )

    answer = n8n_response.get("answer")
    sources = n8n_response.get("sources", [])
    response_type = n8n_response.get("response_type")

    if not answer:
        raise HTTPException(
            status_code=502,
            detail=("Chatbot servisinden geçerli bir " "cevap alınamadı."),
        )

    if not isinstance(sources, list):
        sources = []

    chat_log_id_value = n8n_response.get("chat_log_id")

    chat_log_id: int | None = None

    if response_type != "static_response":
        if isinstance(chat_log_id_value, bool):
            raise HTTPException(
                status_code=502,
                detail=("Chatbot servisinden geçerli bir " "kayıt kimliği alınamadı."),
            )

        try:
            chat_log_id = int(chat_log_id_value)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=502,
                detail=("Chatbot servisinden geçerli bir " "kayıt kimliği alınamadı."),
            )

        if chat_log_id <= 0:
            raise HTTPException(
                status_code=502,
                detail=("Chatbot servisinden geçerli bir " "kayıt kimliği alınamadı."),
            )

    return ChatResponse(
        chat_log_id=chat_log_id,
        question=n8n_response.get(
            "question",
            request.question,
        ),
        answer=answer,
        sources=sources,
        response_type=response_type,
    )
