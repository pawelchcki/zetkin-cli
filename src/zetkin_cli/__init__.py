"""Typed Python access to the Zetkin API."""

from .client import AsyncZetkinClient, ZetkinClient
from .errors import (
    ZetkinAuthError,
    ZetkinConfigError,
    ZetkinError,
    ZetkinHTTPError,
    ZetkinTransportError,
)
from .models import ApiResult, Page

__all__ = [
    "ApiResult",
    "AsyncZetkinClient",
    "Page",
    "ZetkinAuthError",
    "ZetkinClient",
    "ZetkinConfigError",
    "ZetkinError",
    "ZetkinHTTPError",
    "ZetkinTransportError",
]

__version__ = "0.1.0"
