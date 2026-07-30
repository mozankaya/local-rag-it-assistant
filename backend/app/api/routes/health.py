import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.users import require_admin
from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User


router = APIRouter(tags=["Health"])


def healthy(message: str) -> dict[str, str]:
    return {
        "status": "healthy",
        "message": message,
    }


def unavailable(message: str) -> dict[str, str]:
    return {
        "status": "unavailable",
        "message": message,
    }


def check_database(db: Session) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return healthy("PostgreSQL bağlantısı başarılı.")
    except Exception:
        return unavailable("PostgreSQL bağlantısı kurulamadı.")


def check_http_service(
    url: str,
    success_message: str,
    error_message: str,
    timeout_seconds: float,
) -> dict[str, str]:
    try:
        response = httpx.get(
            url,
            timeout=timeout_seconds,
        )
        response.raise_for_status()

        return healthy(success_message)
    except httpx.HTTPError:
        return unavailable(error_message)


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "fastapi-gateway",
    }


@router.get("/admin/system-status")
def get_system_status(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> dict[str, object]:
    settings = get_settings()

    services = {
        "api": healthy("Backend API çalışıyor."),
        "database": check_database(db),
        "n8n": check_http_service(
            url=settings.n8n_health_url,
            success_message="n8n servisine erişilebiliyor.",
            error_message="n8n servisine ulaşılamadı.",
            timeout_seconds=settings.service_status_timeout_seconds,
        ),
        "ollama": check_http_service(
            url=settings.ollama_health_url,
            success_message="Ollama servisine erişilebiliyor.",
            error_message="Ollama servisine ulaşılamadı.",
            timeout_seconds=settings.service_status_timeout_seconds,
        ),
    }

    all_services_healthy = all(
        service["status"] == "healthy"
        for service in services.values()
    )

    return {
        "overall_status": (
            "healthy"
            if all_services_healthy
            else "degraded"
        ),
        "services": services,
    }
