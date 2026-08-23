"""Synchronous and asynchronous HTTP transports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import httpx

from .auth import TokenManager
from .errors import ZetkinHTTPError, ZetkinTransportError
from .models import ApiResult, JsonValue

Params = Mapping[str, str | int | float | bool | None]


class Transport:
    def __init__(
        self,
        base_url: str,
        token_manager: TokenManager | None,
        *,
        timeout: float = 30,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token_manager = token_manager
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout, follow_redirects=False)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        version: int,
        params: Params | None = None,
        json: JsonValue = None,
        data: Mapping[str, str] | None = None,
        content: bytes | None = None,
        files: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> ApiResult[JsonValue | bytes]:
        url = _build_url(self.base_url, version, path)
        request_headers = _safe_headers(headers)
        _authorize(request_headers, self.token_manager)
        try:
            response = self.client.request(
                method.upper(),
                url,
                params=_clean_params(params),
                json=json if json is not None else None,
                data=data,
                content=content,
                files=files,
                headers=request_headers,
            )
            if _should_refresh(response, self.token_manager):
                access_token = self.token_manager.refresh_sync(self.client)  # type: ignore[union-attr]
                request_headers["Authorization"] = f"Bearer {access_token}"
                response = self.client.request(
                    method.upper(),
                    url,
                    params=_clean_params(params),
                    json=json if json is not None else None,
                    data=data,
                    content=content,
                    files=files,
                    headers=request_headers,
                )
        except httpx.HTTPError as exc:
            raise ZetkinTransportError(f"Request failed: {exc}") from exc
        return _parse_response(response)


class AsyncTransport:
    def __init__(
        self,
        base_url: str,
        token_manager: TokenManager | None,
        *,
        timeout: float = 30,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token_manager = token_manager
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=timeout, follow_redirects=False
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        version: int,
        params: Params | None = None,
        json: JsonValue = None,
        data: Mapping[str, str] | None = None,
        content: bytes | None = None,
        files: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> ApiResult[JsonValue | bytes]:
        url = _build_url(self.base_url, version, path)
        request_headers = _safe_headers(headers)
        _authorize(request_headers, self.token_manager)
        try:
            response = await self.client.request(
                method.upper(),
                url,
                params=_clean_params(params),
                json=json if json is not None else None,
                data=data,
                content=content,
                files=files,
                headers=request_headers,
            )
            if _should_refresh(response, self.token_manager):
                access_token = await self.token_manager.refresh_async(self.client)  # type: ignore[union-attr]
                request_headers["Authorization"] = f"Bearer {access_token}"
                response = await self.client.request(
                    method.upper(),
                    url,
                    params=_clean_params(params),
                    json=json if json is not None else None,
                    data=data,
                    content=content,
                    files=files,
                    headers=request_headers,
                )
        except httpx.HTTPError as exc:
            raise ZetkinTransportError(f"Request failed: {exc}") from exc
        return _parse_response(response)


def _build_url(base_url: str, version: int, path: str) -> str:
    if version not in {1, 2}:
        raise ValueError("API version must be 1 or 2")
    clean = path.strip()
    if clean.startswith(("http://", "https://")):
        raise ValueError("Absolute request URLs are not allowed")
    clean = clean.lstrip("/")
    if clean.startswith(("v1/", "v2/")):
        raise ValueError("Pass an unversioned resource path")
    return f"{base_url}/v{version}/{clean}"


def _safe_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    output = {"Accept": "application/json"}
    blocked = {"authorization", "host", "content-length"}
    for key, value in (headers or {}).items():
        if key.lower() in blocked:
            raise ValueError(f"Header {key!r} is managed by the SDK")
        output[key] = value
    return output


def _authorize(headers: dict[str, str], manager: TokenManager | None) -> None:
    if manager and manager.access_token:
        headers["Authorization"] = f"Bearer {manager.access_token}"


def _clean_params(params: Params | None) -> dict[str, str | int | float | bool]:
    return {key: value for key, value in (params or {}).items() if value is not None}


def _should_refresh(response: httpx.Response, manager: TokenManager | None) -> bool:
    if not manager or not manager.can_refresh:
        return False
    if manager.token and manager.token.expired():
        return True
    if response.status_code != 401:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return isinstance(payload, dict) and "invalid_token" in str(
        payload.get("error", "")
    )


def _parse_response(response: httpx.Response) -> ApiResult[JsonValue | bytes]:
    headers = dict(response.headers)
    if response.status_code == 204:
        payload: JsonValue | bytes = None
        meta = None
    elif "json" in response.headers.get("content-type", "").lower():
        try:
            body = response.json()
        except ValueError:
            body = {"error": "invalid_json", "message": response.text}
        if isinstance(body, dict) and "data" in body:
            payload = cast(JsonValue, body["data"])
            raw_meta = body.get("meta")
            meta = raw_meta if isinstance(raw_meta, dict) else None
        else:
            payload = cast(JsonValue, body)
            meta = None
    else:
        payload = response.content
        meta = None
    if response.is_error:
        message = _error_message(payload)
        raise ZetkinHTTPError(
            response.status_code,
            message,
            body=payload,
            request_id=response.headers.get("x-request-id"),
        )
    return ApiResult(
        data=payload,
        status_code=response.status_code,
        headers=headers,
        meta=meta,
    )


def _error_message(payload: JsonValue | bytes) -> str:
    if isinstance(payload, dict):
        for key in ("message", "error_description", "error"):
            if isinstance(payload.get(key), str):
                return str(payload[key])
    if isinstance(payload, bytes):
        return payload.decode(errors="replace")[:500]
    return str(payload)
