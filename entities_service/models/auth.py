"""Auth models."""

from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


class DSAPIRole(StrEnum):
    """Auth roles for the DataSpaces API concerning the Entities Service."""

    ENTITIES_ADMIN = "entities"

    ENTITIES_READ = "entities:read"
    ENTITIES_WRITE = "entities:write"
    ENTITIES_EDIT = "entities:edit"
    ENTITIES_DELETE = "entities:delete"
