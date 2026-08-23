from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from zetkin_cli.auth import (
    MemoryTokenStore,
    OAuthConfig,
    OAuthFlow,
    TokenData,
    TokenManager,
    token_debug_summary,
)
from zetkin_cli.errors import ZetkinAuthError


def test_authorization_url_contains_state_and_redirect() -> None:
    flow = OAuthFlow(OAuthConfig("client", "secret", "http://127.0.0.1:8765/callback"))
    url, state = flow.create_authorization()
    query = parse_qs(urlparse(url).query)

    assert url.startswith("https://api.zetk.in/v1/oauth/authorize/")
    assert query["client_id"] == ["client"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8765/callback"]
    assert query["state"] == [state]
    assert len(state) >= 32


def test_exchange_callback_uses_basic_auth_and_returns_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        expected = base64.b64encode(b"client:secret").decode()
        assert request.headers["Authorization"] == f"Basic {expected}"
        assert b"grant_type=authorization_code" in request.content
        return httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
            },
        )

    flow = OAuthFlow(OAuthConfig("client", "secret", "http://127.0.0.1:8765/callback"))
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        token = flow.exchange_redirect(
            "http://127.0.0.1:8765/callback?code=abc&state=expected",
            expected_state="expected",
            client=client,
        )

    assert token.access_token == "access"
    assert token.refresh_token == "refresh"
    assert token.expires_at is not None


def test_exchange_rejects_mismatched_state_before_http() -> None:
    flow = OAuthFlow(OAuthConfig("client", "secret", "https://example.test/cb"))
    with pytest.raises(ZetkinAuthError, match="state did not match"):
        flow.exchange_redirect(
            "https://example.test/cb?code=abc&state=wrong",
            expected_state="expected",
        )


def test_refresh_rotates_token_and_preserves_refresh_token() -> None:
    store = MemoryTokenStore()
    store.save("default", TokenData(access_token="old", refresh_token="refresh"))
    manager = TokenManager(
        "default",
        store,
        oauth=OAuthConfig("client", "secret", "https://example.test/cb"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "new", "expires_in": 60})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert manager.refresh_sync(client) == "new"

    assert store.load("default") == manager.token
    assert manager.token and manager.token.refresh_token == "refresh"


def test_token_summary_never_contains_secret_values() -> None:
    summary = token_debug_summary(
        TokenData(access_token="do-not-print", refresh_token="also-secret")
    )
    rendered = str(summary)
    assert "do-not-print" not in rendered
    assert "also-secret" not in rendered
