"""OAuth 2.0 login, refresh, and secure token persistence."""

from __future__ import annotations

import os
import secrets
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Protocol, Self
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import keyring
from keyring.errors import KeyringError
from pydantic import BaseModel, ConfigDict

from .errors import ZetkinAuthError, ZetkinConfigError

KEYRING_SERVICE = "zetkin-cli"


class TokenData(BaseModel):
    model_config = ConfigDict(extra="allow")

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int | None = None
    expires_at: float | None = None

    @classmethod
    def from_response(cls, payload: object, previous: Self | None = None) -> Self:
        if not isinstance(payload, dict):
            raise ZetkinAuthError("The token endpoint returned an invalid response")
        data = dict(payload)
        if not data.get("refresh_token") and previous and previous.refresh_token:
            data["refresh_token"] = previous.refresh_token
        if data.get("expires_in") is not None:
            data["expires_at"] = time.time() + int(data["expires_in"])
        try:
            return cls.model_validate(data)
        except ValueError as exc:
            raise ZetkinAuthError(
                "The token response did not contain an access token"
            ) from exc

    def expired(self, leeway: int = 30) -> bool:
        return self.expires_at is not None and time.time() >= self.expires_at - leeway


class TokenStore(Protocol):
    def load(self, profile: str) -> TokenData | None: ...

    def save(self, profile: str, token: TokenData) -> None: ...

    def delete(self, profile: str) -> None: ...


class KeyringTokenStore:
    def load(self, profile: str) -> TokenData | None:
        try:
            value = keyring.get_password(KEYRING_SERVICE, profile)
        except KeyringError as exc:
            raise ZetkinAuthError(f"Could not read the OS keyring: {exc}") from exc
        if not value:
            return None
        try:
            return TokenData.model_validate_json(value)
        except ValueError as exc:
            raise ZetkinAuthError("The stored OAuth token is invalid") from exc

    def save(self, profile: str, token: TokenData) -> None:
        try:
            keyring.set_password(KEYRING_SERVICE, profile, token.model_dump_json())
        except KeyringError as exc:
            raise ZetkinAuthError(f"Could not write to the OS keyring: {exc}") from exc

    def delete(self, profile: str) -> None:
        try:
            if keyring.get_password(KEYRING_SERVICE, profile) is not None:
                keyring.delete_password(KEYRING_SERVICE, profile)
        except KeyringError as exc:
            raise ZetkinAuthError(f"Could not update the OS keyring: {exc}") from exc


class MemoryTokenStore:
    def __init__(self) -> None:
        self.tokens: dict[str, TokenData] = {}

    def load(self, profile: str) -> TokenData | None:
        return self.tokens.get(profile)

    def save(self, profile: str, token: TokenData) -> None:
        self.tokens[profile] = token

    def delete(self, profile: str) -> None:
        self.tokens.pop(profile, None)


@dataclass(frozen=True, slots=True)
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    base_url: str = "https://api.zetk.in"

    @classmethod
    def from_env(cls, *, base_url: str, redirect_uri: str | None) -> Self:
        client_id = os.getenv("ZETKIN_CLIENT_ID")
        client_secret = os.getenv("ZETKIN_CLIENT_SECRET")
        final_redirect = os.getenv("ZETKIN_REDIRECT_URI") or redirect_uri
        missing = [
            name
            for name, value in (
                ("ZETKIN_CLIENT_ID", client_id),
                ("ZETKIN_CLIENT_SECRET", client_secret),
                ("ZETKIN_REDIRECT_URI", final_redirect),
            )
            if not value
        ]
        if missing:
            raise ZetkinConfigError(
                "Missing OAuth configuration: " + ", ".join(missing)
            )
        return cls(
            client_id=client_id or "",
            client_secret=client_secret or "",
            redirect_uri=final_redirect or "",
            base_url=base_url.rstrip("/"),
        )

    @property
    def authorize_url(self) -> str:
        return f"{self.base_url}/v1/oauth/authorize/"

    @property
    def token_url(self) -> str:
        return f"{self.base_url}/v1/oauth/token/"


class TokenManager:
    def __init__(
        self,
        profile: str,
        store: TokenStore,
        *,
        oauth: OAuthConfig | None = None,
        access_token: str | None = None,
    ) -> None:
        self.profile = profile
        self.store = store
        self.oauth = oauth
        self._external = access_token is not None
        self.token = (
            TokenData(access_token=access_token)
            if access_token
            else store.load(profile)
        )

    @property
    def access_token(self) -> str | None:
        return self.token.access_token if self.token else None

    @property
    def can_refresh(self) -> bool:
        return bool(
            not self._external
            and self.oauth
            and self.token
            and self.token.refresh_token
        )

    def save(self, token: TokenData) -> None:
        self.token = token
        if not self._external:
            self.store.save(self.profile, token)

    def refresh_sync(self, client: httpx.Client) -> str:
        if not self.can_refresh or not self.oauth or not self.token:
            raise ZetkinAuthError("No refreshable OAuth token is available")
        response = client.post(
            self.oauth.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.token.refresh_token,
            },
            auth=httpx.BasicAuth(self.oauth.client_id, self.oauth.client_secret),
        )
        token = _token_from_http_response(response, self.token)
        self.save(token)
        return token.access_token

    async def refresh_async(self, client: httpx.AsyncClient) -> str:
        if not self.can_refresh or not self.oauth or not self.token:
            raise ZetkinAuthError("No refreshable OAuth token is available")
        response = await client.post(
            self.oauth.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.token.refresh_token,
            },
            auth=httpx.BasicAuth(self.oauth.client_id, self.oauth.client_secret),
        )
        token = _token_from_http_response(response, self.token)
        self.save(token)
        return token.access_token


class OAuthFlow:
    def __init__(self, config: OAuthConfig) -> None:
        self.config = config

    def create_authorization(self) -> tuple[str, str]:
        state = secrets.token_urlsafe(32)
        query = urlencode(
            {
                "client_id": self.config.client_id,
                "redirect_uri": self.config.redirect_uri,
                "response_type": "code",
                "scope": "",
                "state": state,
            }
        )
        return f"{self.config.authorize_url}?{query}", state

    def open_and_receive_loopback(
        self,
        authorization_url: str,
        *,
        timeout: float = 180,
        opener: Callable[[str], bool] = webbrowser.open,
    ) -> str | None:
        target = urlparse(self.config.redirect_uri)
        if target.scheme != "http" or target.hostname not in {"127.0.0.1", "localhost"}:
            opener(authorization_url)
            return None
        port = target.port or 80
        captured: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                host = self.headers.get("Host", f"{target.hostname}:{port}")
                captured.append(f"http://{host}{self.path}")
                message = b"Authentication received. You can close this window."
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(message)))
                self.end_headers()
                self.wfile.write(message)

            def log_message(self, format: str, *args: object) -> None:
                return

        try:
            server = HTTPServer((target.hostname, port), Handler)
        except OSError:
            opener(authorization_url)
            return None
        server.timeout = timeout
        try:
            opener(authorization_url)
            server.handle_request()
        finally:
            server.server_close()
        return captured[0] if captured else None

    def exchange_redirect(
        self,
        redirected_url: str,
        *,
        expected_state: str,
        client: httpx.Client | None = None,
    ) -> TokenData:
        parsed = urlparse(redirected_url)
        values = parse_qs(parsed.query)
        if values.get("state", [None])[0] != expected_state:
            raise ZetkinAuthError("OAuth state did not match; refusing the callback")
        if error := values.get("error", [None])[0]:
            description = values.get("error_description", [error])[0]
            raise ZetkinAuthError(f"OAuth authorization failed: {description}")
        code = values.get("code", [None])[0]
        if not code:
            raise ZetkinAuthError("The OAuth callback did not contain a code")
        owns_client = client is None
        http = client or httpx.Client(timeout=30)
        try:
            response = http.post(
                self.config.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.config.redirect_uri,
                },
                auth=httpx.BasicAuth(self.config.client_id, self.config.client_secret),
            )
            return _token_from_http_response(response)
        finally:
            if owns_client:
                http.close()


def _token_from_http_response(
    response: httpx.Response, previous: TokenData | None = None
) -> TokenData:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ZetkinAuthError(
            f"Token endpoint returned HTTP {response.status_code} with invalid JSON"
        ) from exc
    if response.is_error:
        message = payload.get("error_description") or payload.get("error")
        if not isinstance(message, str):
            message = f"HTTP {response.status_code}"
        raise ZetkinAuthError(f"Token exchange failed: {message}")
    return TokenData.from_response(payload, previous)


def token_debug_summary(token: TokenData | None) -> dict[str, object]:
    """Return safe status information without revealing either token."""
    if token is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "expires_at": token.expires_at,
        "expired": token.expired(),
        "refreshable": bool(token.refresh_token),
        "token_type": token.token_type,
    }
