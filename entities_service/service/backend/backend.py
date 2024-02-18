"""Generic backend class for the Entities Service."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import BaseModel

from entities_service.models import (
    SOFTModelTypes,
    VersionedSOFTEntity,
    get_uri,
    soft_entity,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator, Iterator
    from typing import Any

    from pydantic import AnyHttpUrl


LOGGER = logging.getLogger(__name__)


# Exceptions
class BackendError(Exception):
    """Any backend error exception."""


class BackendWriteAccessError(BackendError):
    """Exception raised when write access is denied."""


class MalformedResource(BackendError):
    """Exception raised when a resource is malformed."""


# Data models
class BackendSettings(BaseModel):
    """Settings for the backend."""


# Backend class
class Backend(ABC):
    """Interface/ABC for a backend."""

    _settings_model: type[BackendSettings] = BackendSettings
    _settings: BackendSettings

    def __init__(
        self,
        settings: BackendSettings | dict[str, Any] | None = None,
    ) -> None:
        if isinstance(settings, dict):
            settings = self._settings_model(**settings)

        self._settings = settings or self._settings_model()
        self._is_closed: bool = False

    # Exceptions
    @property
    @abstractmethod
    def write_access_exception(self) -> tuple:  # pragma: no cover
        """Get the exception type raised when write access is denied."""
        raise NotImplementedError

    # Standard magic methods
    def __repr__(self) -> str:
        return f"<{self}>"

    def __str__(self) -> str:
        return self.__class__.__name__

    def __del__(self) -> None:
        if not self._is_closed:
            self.close()

    # Container protocol methods
    def __contains__(self, item: Any) -> bool:
        if isinstance(item, dict):
            # Convert to SOFT Entity
            item_or_errors = soft_entity(return_errors=True, **item)
            if isinstance(item_or_errors, list):
                LOGGER.error(
                    "item given to __contains__ is malformed, not a SOFT entity.\n"
                    "Item: %r\nErrors: %s",
                    item,
                    item_or_errors,
                )
                return False
            item = item_or_errors

        if isinstance(item, str):
            # Expect it to be a URI - let the backend handle validation
            return self.read(item) is not None

        if isinstance(item, SOFTModelTypes):
            return self.read(get_uri(item)) is not None

        return False

    @abstractmethod
    def __iter__(self) -> Iterator[dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:  # pragma: no cover
        raise NotImplementedError

    # Backend methods (initialization)
    @abstractmethod
    def initialize(self) -> None:  # pragma: no cover
        """Initialize the backend."""
        raise NotImplementedError

    # Backend methods (CRUD)
    @abstractmethod
    def create(
        self, entities: Sequence[VersionedSOFTEntity | dict[str, Any]]
    ) -> list[dict[str, Any]] | dict[str, Any] | None:  # pragma: no cover
        """Create an entity in the backend."""
        raise NotImplementedError

    @abstractmethod
    def read(
        self, entity_identity: AnyHttpUrl | str
    ) -> dict[str, Any] | None:  # pragma: no cover
        """Read an entity from the backend."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        entity_identity: AnyHttpUrl | str,
        entity: VersionedSOFTEntity | dict[str, Any],
    ) -> None:  # pragma: no cover
        """Update an entity in the backend."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self, entity_identities: Sequence[AnyHttpUrl | str]
    ) -> None:  # pragma: no cover
        """Delete an entity in the backend."""
        raise NotImplementedError

    # Backend methods (search)
    @abstractmethod
    def search(
        self,
        raw_query: Any = None,
        by_properties: list[str] | None = None,
        by_dimensions: list[str] | None = None,
        by_identity: list[str] | None = None,
    ) -> Generator[dict[str, Any], None, None]:  # pragma: no cover
        """Search for entities.

        If `raw_query` is given, it will be used as the query. Otherwise, the
        `by_properties`, `by_dimensions`, and `by_identity` will be used to
        construct the query.

        If no arguments are given, all entities will be returned.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self, raw_query: Any = None) -> int:  # pragma: no cover
        """Count entities.

        If `raw_query` is not given, all entities will be counted.
        """
        raise NotImplementedError

    # Backend methods (close)
    @property
    def is_closed(self) -> bool:
        """Return True if the backend is closed."""
        return self._is_closed

    def close(self) -> None:
        """Close the backend."""
        if self.is_closed:
            raise BackendError("Backend is already closed")

        self._is_closed = True
