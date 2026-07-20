from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.n8n_client import N8nClientError, post_to_n8n


app = FastAPI(
    title="İZELTAŞ IT Asistanı API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "fastapi-gateway",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    if len(request.question) > settings.max_question_length:
        raise HTTPException(
            status_code=400,
            detail="Soru çok uzun. Lütfen daha kısa bir soru girin.",
        )

    payload = {
        "question": request.question,
    }

    try:
        n8n_response = await post_to_n8n(
            url=settings.n8n_rag_webhook_url,
            payload=payload,
            timeout_seconds=settings.request_timeout_seconds,
        )

    except N8nClientError:
        raise HTTPException(
            status_code=502,
            detail="Chatbot servisine şu anda ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
        )

    answer = n8n_response.get("answer")
    sources = n8n_response.get("sources", [])

    if not answer:
        raise HTTPException(
            status_code=502,
            detail="Chatbot servisinden geçerli bir cevap alınamadı.",
        )

    if not isinstance(sources, list):
        sources = []

    return ChatResponse(
        question=n8n_response.get("question", request.question),
        answer=answer,
        sources=sources,
    )


@app.post("/feedback", response_model=FeedbackResponse)
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