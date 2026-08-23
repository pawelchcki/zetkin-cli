"""Top-level synchronous and asynchronous Zetkin clients."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Self

import httpx

from .auth import KeyringTokenStore, OAuthConfig, TokenManager, TokenStore
from .config import ConfigStore
from .models import (
    ApiResult,
    Area,
    JsonValue,
    Page,
    Person,
    PersonCreate,
    SmartSearch,
    Tag,
)
from .services import AsyncV1Namespace, AsyncV2Namespace, V1Namespace, V2Namespace
from .transport import AsyncTransport, Params, Transport


def _optional_oauth(base_url: str, redirect_uri: str | None) -> OAuthConfig | None:
    client_id = os.getenv("ZETKIN_CLIENT_ID")
    client_secret = os.getenv("ZETKIN_CLIENT_SECRET")
    final_redirect = os.getenv("ZETKIN_REDIRECT_URI") or redirect_uri
    if client_id and client_secret and final_redirect:
        return OAuthConfig(client_id, client_secret, final_redirect, base_url)
    return None


class ZetkinClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.zetk.in",
        profile: str = "default",
        access_token: str | None = None,
        oauth: OAuthConfig | None = None,
        token_store: TokenStore | None = None,
        timeout: float = 30,
        http_client: httpx.Client | None = None,
    ) -> None:
        store = token_store or KeyringTokenStore()
        manager = TokenManager(
            profile,
            store,
            oauth=oauth,
            access_token=access_token,
        )
        self.profile = profile
        self.base_url = base_url.rstrip("/")
        self.token_manager = manager
        self._transport = Transport(
            self.base_url,
            manager,
            timeout=timeout,
            client=http_client,
        )
        self.v1 = V1Namespace(self)
        self.v2 = V2Namespace(self)

    @classmethod
    def from_env(
        cls,
        *,
        profile: str | None = None,
        config_store: ConfigStore | None = None,
        token_store: TokenStore | None = None,
        timeout: float = 30,
        http_client: httpx.Client | None = None,
    ) -> Self:
        selected = (config_store or ConfigStore()).get(profile)
        return cls(
            base_url=selected.base_url,
            profile=selected.name,
            access_token=os.getenv("ZETKIN_ACCESS_TOKEN"),
            oauth=_optional_oauth(selected.base_url, selected.redirect_uri),
            token_store=token_store,
            timeout=timeout,
            http_client=http_client,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        version: int = 1,
        params: Params | None = None,
        json: JsonValue = None,
        data: Mapping[str, str] | None = None,
        content: bytes | None = None,
        files: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> ApiResult[JsonValue | bytes]:
        return self._transport.request(
            method,
            path,
            version=version,
            params=params,
            json=json,
            data=data,
            content=content,
            files=files,
            headers=headers,
        )

    def for_org(self, org_id: int) -> OrganizationClient:
        return OrganizationClient(self, org_id)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncZetkinClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.zetk.in",
        profile: str = "default",
        access_token: str | None = None,
        oauth: OAuthConfig | None = None,
        token_store: TokenStore | None = None,
        timeout: float = 30,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        store = token_store or KeyringTokenStore()
        manager = TokenManager(
            profile,
            store,
            oauth=oauth,
            access_token=access_token,
        )
        self.profile = profile
        self.base_url = base_url.rstrip("/")
        self.token_manager = manager
        self._transport = AsyncTransport(
            self.base_url,
            manager,
            timeout=timeout,
            client=http_client,
        )
        self.v1 = AsyncV1Namespace(self)
        self.v2 = AsyncV2Namespace(self)

    @classmethod
    def from_env(
        cls,
        *,
        profile: str | None = None,
        config_store: ConfigStore | None = None,
        token_store: TokenStore | None = None,
        timeout: float = 30,
        http_client: httpx.AsyncClient | None = None,
    ) -> Self:
        selected = (config_store or ConfigStore()).get(profile)
        return cls(
            base_url=selected.base_url,
            profile=selected.name,
            access_token=os.getenv("ZETKIN_ACCESS_TOKEN"),
            oauth=_optional_oauth(selected.base_url, selected.redirect_uri),
            token_store=token_store,
            timeout=timeout,
            http_client=http_client,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        version: int = 1,
        params: Params | None = None,
        json: JsonValue = None,
        data: Mapping[str, str] | None = None,
        content: bytes | None = None,
        files: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> ApiResult[JsonValue | bytes]:
        return await self._transport.request(
            method,
            path,
            version=version,
            params=params,
            json=json,
            data=data,
            content=content,
            files=files,
            headers=headers,
        )

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


class OrganizationClient:
    """Organization-bound facade over the most common organizer services."""

    def __init__(self, client: ZetkinClient, org_id: int) -> None:
        self.client = client
        self.org_id = org_id
        self.people = _BoundPeople(self)
        self.tags = _BoundTags(self)
        self.smart_searches = _BoundSearches(self)
        self.campaigns = _BoundCollection(self, client.v1.campaigns)
        self.events = _BoundCollection(self, client.v1.events)
        self.surveys = _BoundCollection(self, client.v1.surveys)
        self.areas = _BoundAreas(self)
        self.canvass = client.v2


class _BoundPeople:
    def __init__(self, org: OrganizationClient) -> None:
        self._org = org

    def list(self, **kwargs: Any) -> Page[Person]:
        return self._org.client.v1.people.list(self._org.org_id, **kwargs)

    def get(self, person_id: int) -> Person:
        return self._org.client.v1.people.get(self._org.org_id, person_id)

    def create(self, data: PersonCreate | dict[str, JsonValue]) -> Person:
        return self._org.client.v1.people.create(self._org.org_id, data)

    def update(self, person_id: int, data: dict[str, JsonValue]) -> Person:
        return self._org.client.v1.people.update(self._org.org_id, person_id, data)

    def delete(self, person_id: int) -> None:
        self._org.client.v1.people.delete(self._org.org_id, person_id)


class _BoundTags:
    def __init__(self, org: OrganizationClient) -> None:
        self._org = org

    def list(self) -> Page[Tag]:
        return self._org.client.v1.tags.list(self._org.org_id)

    def add_to_person(self, person_id: int, tag_id: int) -> None:
        self._org.client.v1.tags.add_to_person(self._org.org_id, person_id, tag_id)

    def remove_from_person(self, person_id: int, tag_id: int) -> None:
        self._org.client.v1.tags.remove_from_person(self._org.org_id, person_id, tag_id)


class _BoundSearches:
    def __init__(self, org: OrganizationClient) -> None:
        self._org = org

    def list(self) -> Page[SmartSearch]:
        return self._org.client.v1.smart_searches.list(self._org.org_id)

    def search(self, data_type: str, query: str) -> JsonValue:
        return self._org.client.v1.smart_searches.search(
            self._org.org_id, data_type, query
        )


class _BoundCollection:
    def __init__(self, org: OrganizationClient, service: Any) -> None:
        self._org = org
        self._service = service

    def list(self, **kwargs: Any) -> object:
        return self._service.list(self._org.org_id, **kwargs)

    def get(self, item_id: int) -> object:
        return self._service.get(self._org.org_id, item_id)

    def create(self, data: dict[str, JsonValue]) -> object:
        return self._service.create(self._org.org_id, data)

    def update(self, item_id: int, data: dict[str, JsonValue]) -> object:
        return self._service.update(self._org.org_id, item_id, data)

    def delete(self, item_id: int) -> None:
        self._service.delete(self._org.org_id, item_id)


class _BoundAreas:
    def __init__(self, org: OrganizationClient) -> None:
        self._org = org

    def list(self, **kwargs: Any) -> Page[Area]:
        return self._org.client.v2.areas.list(self._org.org_id, **kwargs)

    def create(self, data: dict[str, JsonValue]) -> Area:
        return self._org.client.v2.areas.create(self._org.org_id, data)

    def update(self, area_id: int, data: dict[str, JsonValue]) -> Area:
        return self._org.client.v2.areas.update(self._org.org_id, area_id, data)

    def delete(self, area_id: int) -> None:
        self._org.client.v2.areas.delete(self._org.org_id, area_id)
