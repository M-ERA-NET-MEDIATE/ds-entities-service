"""Auth models."""

from __future__ import annotations

from enum import StrEnum


class DSAPIRole(StrEnum):
    """Auth roles for the DataSpaces API concerning the Entities Service."""

    ENTITIES_ADMIN = "entities"

    ENTITIES_READ = "entities:read"
    ENTITIES_WRITE = "entities:write"
    ENTITIES_EDIT = "entities:edit"
    ENTITIES_DELETE = "entities:delete"
