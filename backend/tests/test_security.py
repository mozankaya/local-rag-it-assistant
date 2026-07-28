from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core import security
from app.core.config import get_settings


def test_create_and_decode_access_token() -> None:
    token = security.create_access_token(
        subject="user@example.com",
        extra_data={
            "role": "user",
        },
    )

    payload = security.decode_access_token(token)

    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "user"
    assert "exp" in payload


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(ValueError, match="Invalid token"):
        security.decode_access_token("not-a-valid-jwt-token")


def test_decode_access_token_rejects_expired_token() -> None:
    settings = get_settings()

    expired_payload = {
        "sub": "user@example.com",
        "role": "user",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError, match="Invalid token"):
        security.decode_access_token(expired_token)