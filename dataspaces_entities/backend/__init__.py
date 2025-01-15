"""Backend module.

Currently implemented backends:

- MongoDB

"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Enum with string values."""


if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from dataspaces_entities.backend.backend import Backend


class Backends(StrEnum):
    """Backends."""

    MONGODB = "mongodb"

    def get_class(self) -> type[Backend]:
        """Get the backend class."""
        if self == self.MONGODB:
            from dataspaces_entities.backend.mongodb import MongoDBBackend

            return MongoDBBackend

        raise NotImplementedError(f"Backend {self} not implemented")

    def get_default_settings(self) -> dict[str, Any]:
        """Get the default settings for the given backend."""
        # Import `get_config` here to avoid circular imports
        from dataspaces_entities.config import get_config

        config = get_config()

        if self == self.MONGODB:
            return {
                "mongo_username": config.mongo_user,
                "mongo_password": config.mongo_password,
            }

        raise NotImplementedError(f"Backend {self} not implemented")


def get_backend(
    backend: Backends | str | None = None,
    settings: dict[str, Any] | None = None,
) -> Backend:
    """Get a backend instance."""
    # Import `get_config` here to avoid circular imports
    from dataspaces_entities.config import get_config

    if backend is None:
        backend = get_config().backend

    try:
        backend = Backends(backend)
    except ValueError as exc:
        raise ValueError(
            f"Unknown backend: {backend}\nValid backends:\n"
            + "\n".join(f" - {_}" for _ in Backends.__members__.values())
        ) from exc

    backend_class = backend.get_class()

    backend_settings = backend.get_default_settings()
    if isinstance(settings, dict):
        backend_settings.update(settings)

    return backend_class(settings=backend_settings)
