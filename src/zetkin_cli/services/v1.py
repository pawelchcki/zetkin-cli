"""Friendly services for documented Zetkin API v1 resources."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping

from zetkin_cli.generated import AsyncV1Operations, V1Operations
from zetkin_cli.models import (
    Campaign,
    Event,
    JsonValue,
    Organization,
    OrganizationCreate,
    Page,
    Person,
    PersonCreate,
    SmartSearch,
    Survey,
    Tag,
    User,
)
from zetkin_cli.transport import Params

from .base import (
    AsyncRequester,
    SyncRequester,
    json_data,
    json_object,
    model_data,
    page_data,
)


class OrganizationsService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(self, *, params: Params | None = None) -> Page[Organization]:
        return page_data(
            self._client.request("GET", "/orgs", version=1, params=params),
            Organization,
        )

    def get(self, org_id: int) -> Organization:
        return model_data(
            self._client.request("GET", f"/orgs/{org_id}", version=1),
            Organization,
        )

    def create(self, data: OrganizationCreate | dict[str, JsonValue]) -> Organization:
        return model_data(
            self._client.request("POST", "/orgs", version=1, json=json_object(data)),
            Organization,
        )

    def update(self, org_id: int, data: dict[str, JsonValue]) -> Organization:
        return model_data(
            self._client.request("PATCH", f"/orgs/{org_id}", version=1, json=data),
            Organization,
        )

    def delete(self, org_id: int) -> None:
        self._client.request("DELETE", f"/orgs/{org_id}", version=1)


class PeopleService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(
        self,
        org_id: int,
        *,
        page: int = 0,
        per_page: int = 50,
        params: Params | None = None,
    ) -> Page[Person]:
        query: dict[str, str | int | float | bool | None] = dict(params or {})
        query.update(p=page, pp=per_page)
        return page_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/people", version=1, params=query
            ),
            Person,
        )

    def iter_all(
        self, org_id: int, *, per_page: int = 100, params: Params | None = None
    ) -> Iterator[Person]:
        page = 0
        while True:
            result = self.list(
                org_id, page=page, per_page=per_page, params=params
            ).items
            yield from result
            if len(result) < per_page:
                return
            page += 1

    def get(self, org_id: int, person_id: int) -> Person:
        return model_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/people/{person_id}", version=1
            ),
            Person,
        )

    def create(self, org_id: int, data: PersonCreate | dict[str, JsonValue]) -> Person:
        return model_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/people",
                version=1,
                json=json_object(data),
            ),
            Person,
        )

    def update(self, org_id: int, person_id: int, data: dict[str, JsonValue]) -> Person:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/people/{person_id}",
                version=1,
                json=data,
            ),
            Person,
        )

    def delete(self, org_id: int, person_id: int) -> None:
        self._client.request("DELETE", f"/orgs/{org_id}/people/{person_id}", version=1)


class TagsService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(self, org_id: int) -> Page[Tag]:
        return page_data(
            self._client.request("GET", f"/orgs/{org_id}/people/tags", version=1),
            Tag,
        )

    def get(self, org_id: int, tag_id: int) -> Tag:
        return model_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/people/tags/{tag_id}", version=1
            ),
            Tag,
        )

    def create(self, org_id: int, data: dict[str, JsonValue]) -> Tag:
        return model_data(
            self._client.request(
                "POST", f"/orgs/{org_id}/people/tags", version=1, json=data
            ),
            Tag,
        )

    def update(self, org_id: int, tag_id: int, data: dict[str, JsonValue]) -> Tag:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/people/tags/{tag_id}",
                version=1,
                json=data,
            ),
            Tag,
        )

    def add_to_person(self, org_id: int, person_id: int, tag_id: int) -> None:
        self._client.request(
            "PUT",
            f"/orgs/{org_id}/people/{person_id}/tags/{tag_id}",
            version=1,
        )

    def remove_from_person(self, org_id: int, person_id: int, tag_id: int) -> None:
        self._client.request(
            "DELETE",
            f"/orgs/{org_id}/people/{person_id}/tags/{tag_id}",
            version=1,
        )

    def delete(self, org_id: int, tag_id: int) -> None:
        self._client.request(
            "DELETE", f"/orgs/{org_id}/people/tags/{tag_id}", version=1
        )


class SmartSearchesService:
    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def list(self, org_id: int) -> Page[SmartSearch]:
        return page_data(
            self._client.request("GET", f"/orgs/{org_id}/people/queries", version=1),
            SmartSearch,
        )

    def get(self, org_id: int, query_id: int) -> SmartSearch:
        return model_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/people/queries/{query_id}",
                version=1,
            ),
            SmartSearch,
        )

    def create(self, org_id: int, data: dict[str, JsonValue]) -> SmartSearch:
        return model_data(
            self._client.request(
                "POST", f"/orgs/{org_id}/people/queries", version=1, json=data
            ),
            SmartSearch,
        )

    def matches(
        self, org_id: int, query_id: int, *, params: Params | None = None
    ) -> Page[Person]:
        return page_data(
            self._client.request(
                "GET",
                f"/orgs/{org_id}/people/queries/{query_id}/matches",
                version=1,
                params=params,
            ),
            Person,
        )

    def search(self, org_id: int, data_type: str, query: str) -> JsonValue:
        return json_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/search/{data_type}",
                version=1,
                json={"q": query},
            )
        )


class _OrgCollectionService[M: Campaign | Event | Survey]:
    def __init__(
        self,
        client: SyncRequester,
        resource: str,
        model: type[M],
    ) -> None:
        self._client = client
        self._resource = resource
        self._model = model

    def list(self, org_id: int, *, params: Params | None = None) -> Page[M]:
        return page_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/{self._resource}", version=1, params=params
            ),
            self._model,
        )

    def get(self, org_id: int, item_id: int) -> M:
        return model_data(
            self._client.request(
                "GET", f"/orgs/{org_id}/{self._resource}/{item_id}", version=1
            ),
            self._model,
        )

    def create(self, org_id: int, data: dict[str, JsonValue]) -> M:
        return model_data(
            self._client.request(
                "POST",
                f"/orgs/{org_id}/{self._resource}",
                version=1,
                json=data,
            ),
            self._model,
        )

    def update(self, org_id: int, item_id: int, data: dict[str, JsonValue]) -> M:
        return model_data(
            self._client.request(
                "PATCH",
                f"/orgs/{org_id}/{self._resource}/{item_id}",
                version=1,
                json=data,
            ),
            self._model,
        )

    def delete(self, org_id: int, item_id: int) -> None:
        self._client.request(
            "DELETE", f"/orgs/{org_id}/{self._resource}/{item_id}", version=1
        )


class SectionService:
    """Convenient version-bound access to less common resource families."""

    def __init__(self, client: SyncRequester) -> None:
        self._client = client

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Params | None = None,
        json: JsonValue = None,
    ) -> JsonValue | bytes:
        return self._client.request(
            method, path, version=1, params=params, json=json
        ).data


class V1Namespace:
    def __init__(self, client: SyncRequester) -> None:
        self.ops = V1Operations(client)
        self.organizations = OrganizationsService(client)
        self.people = PeopleService(client)
        self.tags = TagsService(client)
        self.smart_searches = SmartSearchesService(client)
        self.campaigns = _OrgCollectionService(client, "campaigns", Campaign)
        self.events = _OrgCollectionService(client, "actions", Event)
        self.surveys = _OrgCollectionService(client, "surveys", Survey)
        self.calls = SectionService(client)
        self.canvass = SectionService(client)
        self.maps = SectionService(client)
        self.search = SectionService(client)
        self.users = SectionService(client)
        self.views = SectionService(client)

    def current_user(self) -> User:
        return model_data(
            self.ops.get_users_by_user_id(user_id="me"),
            User,
        )


class AsyncOrganizationsService:
    def __init__(self, client: AsyncRequester) -> None:
        self._client = client

    async def list(self, *, params: Params | None = None) -> Page[Organization]:
        return page_data(
            await self._client.request("GET", "/orgs", version=1, params=params),
            Organization,
        )

    async def get(self, org_id: int) -> Organization:
        return model_data(
            await self._client.request("GET", f"/orgs/{org_id}", version=1),
            Organization,
        )

    async def create(
        self, data: OrganizationCreate | dict[str, JsonValue]
    ) -> Organization:
        return model_data(
            await self._client.request(
                "POST", "/orgs", version=1, json=json_object(data)
            ),
            Organization,
        )

    async def update(self, org_id: int, data: dict[str, JsonValue]) -> Organization:
        return model_data(
            await self._client.request(
                "PATCH", f"/orgs/{org_id}", version=1, json=data
            ),
            Organization,
        )

    async def delete(self, org_id: int) -> None:
        await self._client.request("DELETE", f"/orgs/{org_id}", version=1)


class AsyncPeopleService:
    def __init__(self, client: AsyncRequester) -> None:
        self._client = client

    async def list(
        self,
        org_id: int,
        *,
        page: int = 0,
        per_page: int = 50,
        params: Params | None = None,
    ) -> Page[Person]:
        query: dict[str, str | int | float | bool | None] = dict(params or {})
        query.update(p=page, pp=per_page)
        return page_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/people", version=1, params=query
            ),
            Person,
        )

    async def iter_all(
        self, org_id: int, *, per_page: int = 100, params: Params | None = None
    ) -> AsyncIterator[Person]:
        page = 0
        while True:
            items = (
                await self.list(org_id, page=page, per_page=per_page, params=params)
            ).items
            for item in items:
                yield item
            if len(items) < per_page:
                return
            page += 1

    async def get(self, org_id: int, person_id: int) -> Person:
        return model_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/people/{person_id}", version=1
            ),
            Person,
        )

    async def create(
        self, org_id: int, data: PersonCreate | dict[str, JsonValue]
    ) -> Person:
        return model_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/people",
                version=1,
                json=json_object(data),
            ),
            Person,
        )

    async def update(
        self, org_id: int, person_id: int, data: dict[str, JsonValue]
    ) -> Person:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/people/{person_id}",
                version=1,
                json=data,
            ),
            Person,
        )

    async def delete(self, org_id: int, person_id: int) -> None:
        await self._client.request(
            "DELETE", f"/orgs/{org_id}/people/{person_id}", version=1
        )


class AsyncTagsService:
    def __init__(self, client: AsyncRequester) -> None:
        self._client = client

    async def list(self, org_id: int) -> Page[Tag]:
        return page_data(
            await self._client.request("GET", f"/orgs/{org_id}/people/tags", version=1),
            Tag,
        )

    async def add_to_person(self, org_id: int, person_id: int, tag_id: int) -> None:
        await self._client.request(
            "PUT",
            f"/orgs/{org_id}/people/{person_id}/tags/{tag_id}",
            version=1,
        )

    async def remove_from_person(
        self, org_id: int, person_id: int, tag_id: int
    ) -> None:
        await self._client.request(
            "DELETE",
            f"/orgs/{org_id}/people/{person_id}/tags/{tag_id}",
            version=1,
        )


class AsyncSmartSearchesService:
    def __init__(self, client: AsyncRequester) -> None:
        self._client = client

    async def list(self, org_id: int) -> Page[SmartSearch]:
        return page_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/people/queries", version=1
            ),
            SmartSearch,
        )

    async def get(self, org_id: int, query_id: int) -> SmartSearch:
        return model_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/people/queries/{query_id}",
                version=1,
            ),
            SmartSearch,
        )

    async def matches(self, org_id: int, query_id: int) -> Page[Person]:
        return page_data(
            await self._client.request(
                "GET",
                f"/orgs/{org_id}/people/queries/{query_id}/matches",
                version=1,
            ),
            Person,
        )

    async def search(self, org_id: int, data_type: str, query: str) -> JsonValue:
        return json_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/search/{data_type}",
                version=1,
                json={"q": query},
            )
        )


class _AsyncOrgCollectionService[M: Campaign | Event | Survey]:
    def __init__(self, client: AsyncRequester, resource: str, model: type[M]) -> None:
        self._client = client
        self._resource = resource
        self._model = model

    async def list(self, org_id: int, *, params: Params | None = None) -> Page[M]:
        return page_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/{self._resource}", version=1, params=params
            ),
            self._model,
        )

    async def get(self, org_id: int, item_id: int) -> M:
        return model_data(
            await self._client.request(
                "GET", f"/orgs/{org_id}/{self._resource}/{item_id}", version=1
            ),
            self._model,
        )

    async def create(self, org_id: int, data: dict[str, JsonValue]) -> M:
        return model_data(
            await self._client.request(
                "POST",
                f"/orgs/{org_id}/{self._resource}",
                version=1,
                json=data,
            ),
            self._model,
        )

    async def update(self, org_id: int, item_id: int, data: dict[str, JsonValue]) -> M:
        return model_data(
            await self._client.request(
                "PATCH",
                f"/orgs/{org_id}/{self._resource}/{item_id}",
                version=1,
                json=data,
            ),
            self._model,
        )

    async def delete(self, org_id: int, item_id: int) -> None:
        await self._client.request(
            "DELETE", f"/orgs/{org_id}/{self._resource}/{item_id}", version=1
        )


class AsyncSectionService:
    def __init__(self, client: AsyncRequester) -> None:
        self._client = client

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Params | None = None,
        json: JsonValue = None,
    ) -> JsonValue | bytes:
        return (
            await self._client.request(
                method, path, version=1, params=params, json=json
            )
        ).data


class AsyncV1Namespace:
    """Async v1 namespace with full generated operations and common helpers."""

    def __init__(self, client: AsyncRequester) -> None:
        self._client = client
        self.ops = AsyncV1Operations(client)
        self.organizations = AsyncOrganizationsService(client)
        self.people = AsyncPeopleService(client)
        self.tags = AsyncTagsService(client)
        self.smart_searches = AsyncSmartSearchesService(client)
        self.campaigns = _AsyncOrgCollectionService(client, "campaigns", Campaign)
        self.events = _AsyncOrgCollectionService(client, "actions", Event)
        self.surveys = _AsyncOrgCollectionService(client, "surveys", Survey)
        self.calls = AsyncSectionService(client)
        self.canvass = AsyncSectionService(client)
        self.maps = AsyncSectionService(client)
        self.search = AsyncSectionService(client)
        self.users = AsyncSectionService(client)
        self.views = AsyncSectionService(client)

    async def current_user(self) -> User:
        return model_data(
            await self.ops.get_users_by_user_id(user_id="me"),
            User,
        )

    async def list_people(
        self, org_id: int, *, page: int = 0, per_page: int = 50
    ) -> Page[Person]:
        return await self.people.list(org_id, page=page, per_page=per_page)

    async def iter_people(
        self, org_id: int, *, per_page: int = 100
    ) -> AsyncIterator[Person]:
        async for item in self.people.iter_all(org_id, per_page=per_page):
            yield item

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int | float | bool | None] | None = None,
        json: JsonValue = None,
    ) -> JsonValue | bytes:
        return (
            await self._client.request(
                method, path, version=1, params=params, json=json
            )
        ).data
