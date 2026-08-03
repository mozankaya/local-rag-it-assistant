from typing import Any

import httpx

N8N_WEBHOOK_AUTH_HEADER = "X-Internal-Webhook-Key"


class N8nClientError(Exception):
    """n8n bağlantısı veya HTTP isteği başarısız olduğunda kullanılır."""

    pass


class N8nTimeoutError(N8nClientError):
    """n8n isteği zaman aşımına uğradığında kullanılır."""

    pass


def build_webhook_headers(webhook_secret: str) -> dict[str, str]:
    """n8n webhook isteklerinde kullanılacak kimlik doğrulama header'ını oluşturur."""

    return {
        N8N_WEBHOOK_AUTH_HEADER: webhook_secret,
    }


async def post_to_n8n(
    url: str,
    payload: dict[str, Any],
    timeout_seconds: float,
    webhook_secret: str,
) -> dict[str, Any]:
    """n8n webhook'una JSON gönderir ve JSON nesnesi döndürür."""

    headers = build_webhook_headers(webhook_secret)

    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds,
        ) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise N8nClientError("n8n response must be a JSON object.")

            return data

    except httpx.TimeoutException as exc:
        raise N8nTimeoutError("n8n request timed out.") from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        raise N8nClientError(f"n8n returned HTTP {status_code}.") from exc

    except httpx.RequestError as exc:
        raise N8nClientError("n8n request failed.") from exc

    except ValueError as exc:
        raise N8nClientError("n8n returned invalid JSON.") from exc


def trigger_n8n_webhook(
    url: str,
    timeout_seconds: float,
    webhook_secret: str,
) -> None:
    """n8n webhook'unu boş POST isteğiyle çalıştırır."""

    headers = build_webhook_headers(webhook_secret)

    try:
        with httpx.Client(
            timeout=timeout_seconds,
        ) as client:
            response = client.post(
                url,
                content=b"",
                headers=headers,
            )

            response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise N8nTimeoutError("n8n request timed out.") from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        raise N8nClientError(f"n8n returned HTTP {status_code}.") from exc

    except httpx.RequestError as exc:
        raise N8nClientError("n8n request failed.") from exc
