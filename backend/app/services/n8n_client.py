from typing import Any

import httpx

N8N_WEBHOOK_AUTH_HEADER = "X-Internal-Webhook-Key"


class N8nClientError(Exception):
    """Used when the n8n connection or HTTP request fails."""

    pass


class N8nTimeoutError(N8nClientError):
    """It is used when the n8n request times out."""

    pass


def build_webhook_headers(webhook_secret: str) -> dict[str, str]:
    return {
        N8N_WEBHOOK_AUTH_HEADER: webhook_secret,
    }


async def post_to_n8n(
    url: str,
    payload: dict[str, Any],
    timeout_seconds: float,
    webhook_secret: str,
) -> dict[str, Any]:
    """Post JSON to n8n and normalize timeout, HTTP, transport, and JSON failures."""

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
    """Triggers the n8n webhook with an empty POST request."""

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
