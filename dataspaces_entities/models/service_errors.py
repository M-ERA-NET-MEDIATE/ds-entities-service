"""Response errors for the service."""

from __future__ import annotations

from pydantic import BaseModel


class HTTPError(BaseModel):
    """Base class for a generic HTTP error, where a body is allowed."""

    detail: str
