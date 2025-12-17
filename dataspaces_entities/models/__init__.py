"""SOFT models."""

from __future__ import annotations

from .auth import DSAPIRole
from .errors import Error, ErrorResponse
from .service_errors import HTTPError

__all__ = ("DSAPIRole", "Error", "ErrorResponse", "HTTPError")
