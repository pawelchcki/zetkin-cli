"""Exception hierarchy for the SDK and CLI."""

from __future__ import annotations

from typing import Any


class ZetkinError(Exception):
    """Base class for all package-specific errors."""


class ZetkinConfigError(ZetkinError):
    """Configuration is missing or invalid."""


class ZetkinAuthError(ZetkinError):
    """Authentication failed or credentials are unavailable."""


class ZetkinTransportError(ZetkinError):
    """The request could not reach the API."""


class ZetkinHTTPError(ZetkinError):
    """The Zetkin API returned an unsuccessful HTTP response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        body: Any = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(f"Zetkin API returned {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.body = body
        self.request_id = request_id
