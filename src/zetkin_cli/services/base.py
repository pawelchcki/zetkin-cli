"""Helpers shared by friendly service implementations."""

from __future__ import annotations

from typing import Protocol

from zetkin_cli.models import ApiResult, JsonValue, Page, ZetkinModel
from zetkin_cli.transport import Params


class SyncRequester(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        version: int,
        params: Params | None = None,
        json: JsonValue = None,
    ) -> ApiResult[JsonValue | bytes]: ...


class AsyncRequester(Protocol):
    async def request(
        self,
        method: str,
        path: str,
        *,
        version: int,
        params: Params | None = None,
        json: JsonValue = None,
    ) -> ApiResult[JsonValue | bytes]: ...


def model_data[M: ZetkinModel](
    result: ApiResult[JsonValue | bytes], model: type[M]
) -> M:
    if not isinstance(result.data, dict):
        raise ValueError(f"Expected an object response for {model.__name__}")
    return model.model_validate(result.data)


def page_data[M: ZetkinModel](
    result: ApiResult[JsonValue | bytes], model: type[M]
) -> Page[M]:
    if not isinstance(result.data, list):
        raise ValueError(f"Expected a list response for {model.__name__}")
    items = [model.model_validate(item) for item in result.data]
    return Page[M](items=items, meta=result.meta or {})


def json_object(model: ZetkinModel | dict[str, JsonValue]) -> dict[str, JsonValue]:
    if isinstance(model, ZetkinModel):
        return model.model_dump(exclude_none=True)
    return model


def json_data(result: ApiResult[JsonValue | bytes]) -> JsonValue:
    if isinstance(result.data, bytes):
        raise ValueError("Expected a JSON response")
    return result.data
