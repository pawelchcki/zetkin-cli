from __future__ import annotations

import httpx
import pytest

from zetkin_cli.auth import MemoryTokenStore, OAuthConfig, TokenData, TokenManager
from zetkin_cli.errors import ZetkinHTTPError
from zetkin_cli.transport import AsyncTransport, Transport


def test_transport_unwraps_envelope_and_adds_bearer_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.zetk.in/v1/orgs/1?pp=20"
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json={"data": {"id": 1, "title": "Org"}, "meta": {"page": 0}},
        )

    manager = TokenManager("default", MemoryTokenStore(), access_token="token")
    http = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Transport("https://api.zetk.in", manager, client=http)

    result = transport.request("GET", "/orgs/1", version=1, params={"pp": 20})

    assert result.data == {"id": 1, "title": "Org"}
    assert result.meta == {"page": 0}


def test_transport_refreshes_once_after_invalid_token() -> None:
    requests: list[str] = []
    store = MemoryTokenStore()
    store.save("default", TokenData(access_token="old", refresh_token="refresh"))
    manager = TokenManager(
        "default",
        store,
        oauth=OAuthConfig("client", "secret", "https://example.test/cb"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.path.endswith("/oauth/token/"):
            return httpx.Response(
                200,
                json={"access_token": "new", "refresh_token": "next"},
            )
        if request.headers["Authorization"] == "Bearer old":
            return httpx.Response(401, json={"error": "invalid_token"})
        assert request.headers["Authorization"] == "Bearer new"
        return httpx.Response(200, json={"data": {"id": 1}})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    result = Transport("https://api.zetk.in", manager, client=http).request(
        "GET", "/users/me", version=1
    )

    assert result.data == {"id": 1}
    assert len(requests) == 3
    assert manager.token and manager.token.refresh_token == "next"


def test_transport_maps_api_errors() -> None:
    http = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                403,
                json={"error": "forbidden", "message": "No access"},
                headers={"x-request-id": "req-1"},
            )
        )
    )
    transport = Transport("https://api.zetk.in", None, client=http)

    with pytest.raises(ZetkinHTTPError) as raised:
        transport.request("GET", "/orgs/1", version=1)

    assert raised.value.status_code == 403
    assert raised.value.request_id == "req-1"


def test_transport_handles_no_content_and_binary() -> None:
    responses = iter(
        [
            httpx.Response(204),
            httpx.Response(
                200, content=b"image", headers={"content-type": "image/png"}
            ),
        ]
    )
    http = httpx.Client(transport=httpx.MockTransport(lambda request: next(responses)))
    transport = Transport("https://api.zetk.in", None, client=http)

    assert transport.request("DELETE", "/thing", version=1).data is None
    assert transport.request("GET", "/avatar", version=1).data == b"image"


@pytest.mark.asyncio
async def test_async_transport_matches_sync_envelope_behavior() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(200, json={"data": [{"id": 1}], "meta": {}})

    manager = TokenManager("default", MemoryTokenStore(), access_token="token")
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = AsyncTransport("https://api.zetk.in", manager, client=http)
    result = await transport.request("GET", "/orgs", version=1)

    assert result.data == [{"id": 1}]


@pytest.mark.parametrize("path", ["https://evil.test/path", "/v1/orgs", "/v2/areas"])
def test_transport_rejects_unsafe_or_double_versioned_paths(path: str) -> None:
    transport = Transport("https://api.zetk.in", None)
    try:
        with pytest.raises(ValueError):
            transport.request("GET", path, version=1)
    finally:
        transport.close()


def test_transport_rejects_managed_headers() -> None:
    transport = Transport("https://api.zetk.in", None)
    try:
        with pytest.raises(ValueError, match="managed"):
            transport.request(
                "GET", "/orgs", version=1, headers={"Authorization": "bad"}
            )
    finally:
        transport.close()
