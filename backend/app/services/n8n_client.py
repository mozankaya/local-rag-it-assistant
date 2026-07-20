from typing import Any

import httpx


class N8nClientError(Exception):
    pass


async def post_to_n8n(
    url: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise N8nClientError("n8n response must be a JSON object.")

            return data

    except httpx.TimeoutException as exc:
        raise N8nClientError("n8n request timed out.") from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise N8nClientError(f"n8n returned HTTP {status_code}.") from exc

    except httpx.RequestError as exc:
        raise N8nClientError("n8n request failed.") from exc

    except ValueError as exc:
        raise N8nClientError("n8n returned invalid JSON.") from exc