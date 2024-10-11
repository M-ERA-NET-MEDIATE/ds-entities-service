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
    from typing import Any, Literal

    from entities_service.backend.backend import Backend


class Backends(StrEnum):
    """Backends."""

    MONGODB = "mongodb"

    def get_class(self) -> type[Backend]:
        """Get the backend class."""
        if self == self.MONGODB:
            from entities_service.backend.mongodb import MongoDBBackend

            return MongoDBBackend

        raise NotImplementedError(f"Backend {self} not implemented")

    def get_auth_level_settings(self, auth_level: Literal["read", "write"] = "read") -> dict[str, Any]:
        """Get the settings for the auth level."""
        # Import `get_config` here to avoid circular imports
        from entities_service.config import get_config

        config = get_config()

        if self == self.MONGODB:
            if auth_level == "read":
                return {
                    "auth_level": auth_level,
                    "mongo_username": config.mongo_user,
                    "mongo_password": config.mongo_password,
                }

            if auth_level == "write":
                if config.x509_certificate_file is None:
                    raise ValueError("Cannot use 'write' auth level without a X.509 certificate file.")

                return {
                    "auth_level": auth_level,
                    "mongo_username": "Application (not a real user)",
                    "mongo_x509_certificate_file": config.x509_certificate_file,
                    "mongo_ca_file": config.ca_file,
                }

            raise ValueError(f"Unknown auth level: {auth_level!r} (valid: 'read', 'write')")

        raise NotImplementedError(f"Backend {self} not implemented")


def get_backend(
    backend: Backends | str | None = None,
    auth_level: Literal["read", "write"] = "read",
    settings: dict[str, Any] | None = None,
) -> Backend:
    """Get a backend instance."""
    # Import `get_config` here to avoid circular imports
    from entities_service.config import get_config

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

    backend_settings = backend.get_auth_level_settings(auth_level)
    if settings is not None:
        backend_settings.update(settings)

    return backend_class(settings=backend_settings)
