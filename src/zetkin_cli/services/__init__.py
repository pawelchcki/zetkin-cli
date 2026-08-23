"""Friendly versioned API service namespaces."""

from .v1 import AsyncV1Namespace, V1Namespace
from .v2 import AsyncV2Namespace, V2Namespace

__all__ = ["AsyncV1Namespace", "AsyncV2Namespace", "V1Namespace", "V2Namespace"]
