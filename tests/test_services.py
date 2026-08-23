from __future__ import annotations

import httpx
import pytest

from zetkin_cli import AsyncZetkinClient, ZetkinClient
from zetkin_cli.auth import MemoryTokenStore


def test_friendly_v1_people_service_and_bound_facade() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/people"):
            return httpx.Response(
                200,
                json={"data": [{"id": 2, "first_name": "Clara"}]},
            )
        return httpx.Response(
            200,
            json={"data": {"id": 2, "first_name": "Clara"}},
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))
    with ZetkinClient(
        access_token="token", token_store=MemoryTokenStore(), http_client=http
    ) as client:
        people = client.v1.people.list(1)
        person = client.for_org(1).people.get(2)

    assert people.items[0].first_name == "Clara"
    assert person.id == 2
    assert paths == ["/v1/orgs/1/people", "/v1/orgs/1/people/2"]


def test_generated_operation_builds_documented_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/orgs/1/people/2/fields/email"
        return httpx.Response(200, json={"data": "value"})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    with ZetkinClient(
        access_token="token", token_store=MemoryTokenStore(), http_client=http
    ) as client:
        result = (
            client.v1.ops.get_orgs_by_org_id_people_by_person_id_fields_by_field_id(
                org_id=1, person_id=2, field_id="email"
            )
        )

    assert result.data == "value"


def test_v2_area_service_uses_v2_pagination_and_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v2/orgs/1/areas"
        assert dict(request.url.params) == {"page": "2", "size": "25"}
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 3,
                        "organization_id": 1,
                        "title": "North",
                        "boundary": {"type": "Polygon", "coordinates": []},
                    }
                ]
            },
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))
    with ZetkinClient(
        access_token="token", token_store=MemoryTokenStore(), http_client=http
    ) as client:
        page = client.v2.areas.list(1, page=2, size=25)

    assert page.items[0].title == "North"


@pytest.mark.asyncio
async def test_async_clients_expose_v1_and_v2_services() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/users/me":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": 1,
                        "first_name": "Clara",
                        "last_name": "Zetkin",
                    }
                },
            )
        return httpx.Response(200, json={"data": []})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncZetkinClient(
        access_token="token", token_store=MemoryTokenStore(), http_client=http
    ) as client:
        user = await client.v1.current_user()
        areas = await client.v2.areas.list(1)

    assert user.first_name == "Clara"
    assert areas.items == []
