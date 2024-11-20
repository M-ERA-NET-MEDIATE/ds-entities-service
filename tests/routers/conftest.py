"""Pytest fixtures and configuration for service.routers tests."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator
    from pathlib import Path
    from typing import Any

    from pydantic import AnyHttpUrl
    from s7 import SOFT7Entity


@pytest.fixture(autouse=True)
def _mock_backend(
    live_backend: bool,
    backend_test_data: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    static_dir: Path,
) -> None:
    """Mock the backend if not using a live backend."""
    if live_backend:
        return

    from copy import deepcopy

    import yaml
    from pydantic import ConfigDict

    from dataspaces_entities.backend.backend import (
        BackendError,
        BackendSettings,
        BackendWriteAccessError,
    )
    from dataspaces_entities.backend.mongodb import MongoDBBackend
    from dataspaces_entities.models import URI_REGEX
    from dataspaces_entities.utils import get_identity

    class MockBackendError(BackendError):
        """Mock backend error."""

    MockBackendWriteAccessError = (MockBackendError, BackendWriteAccessError)

    class MockSettings(BackendSettings):
        """Mock settings."""

        model_config = ConfigDict(extra="allow")

    class MockBackend(MongoDBBackend):
        """Mock backend."""

        _settings_model: type[MockSettings] = MockSettings
        _settings: MockSettings

        def __init__(self, settings: MockSettings | dict[str, Any] | None = None) -> None:
            super(MongoDBBackend, self).__init__(settings=settings)

            self.__test_data: list[dict[str, Any]] = backend_test_data
            self.__test_data_uris: list[str] = [get_identity(entity) for entity in self.__test_data]

        def __str__(self) -> str:
            return super(MongoDBBackend, self).__str__()

        @property
        def write_access_exception(self) -> tuple:
            return MockBackendWriteAccessError

        @property
        def _test_data(self) -> list[dict[str, Any]]:
            return deepcopy(self.__test_data)

        def __iter__(self) -> Iterator[dict[str, Any]]:
            return iter(self._test_data)

        def __len__(self) -> int:
            return len(self.__test_data)

        def initialize(self) -> None:
            pass

        def create(
            self, entities: Iterable[SOFT7Entity | dict[str, Any]]
        ) -> list[dict[str, Any]] | dict[str, Any] | None:
            """Create entities.

            For testing purposes:
            - Raise an error if entities is/are not part of the `valid_entities.yaml` file.

            """
            valid_entities: list[dict[str, Any]] = yaml.safe_load(
                (static_dir / "valid_entities.yaml").read_text()
            )
            valid_prepared_entities: list[dict[str, Any]] = [
                self._prepare_entity(entity) for entity in valid_entities
            ]

            entities = [self._prepare_entity(entity) for entity in entities]
            entity_identities = [get_identity(entity) for entity in entities]

            if not all(entity in valid_prepared_entities for entity in entities):
                raise MockBackendError(
                    "One or more entities are not part of the `valid_entities.yaml` "
                    "file. Will act like the entities can not be created.\n"
                    f"Entities: {entities}\n"
                    f"Valid entities: {valid_prepared_entities}"
                )

            if not entities:
                return None

            self.__test_data.extend(entities)
            self.__test_data_uris.extend(entity_identities)

            if len(entities) > 1:
                return entities

            return entities[0]

        def read(self, entity_identity: AnyHttpUrl | str) -> dict[str, Any] | None:
            if entity_identity in self.__test_data_uris:
                return self._test_data[self.__test_data_uris.index(entity_identity)]

            return None

        def update(
            self,
            entity_identity: AnyHttpUrl | str,
            entity: SOFT7Entity | dict[str, Any],
        ) -> None:
            if URI_REGEX.match(str(entity_identity)) is None:
                raise MockBackendError(f"Invalid entity identity: {entity_identity}")

            entity = self._prepare_entity(entity)

            if entity_identity in self.__test_data_uris:
                self.__test_data[self.__test_data_uris.index(entity_identity)] = deepcopy(entity)

            return

        def delete(self, entity_identities: Iterable[AnyHttpUrl | str]) -> None:
            if any(URI_REGEX.match(str(identity)) is None for identity in entity_identities):
                raise MockBackendError("One or more invalid entity identities given.")

            for identity in entity_identities:
                if identity in self.__test_data_uris:
                    self.__test_data.pop(self.__test_data_uris.index(identity))
                    self.__test_data_uris.remove(identity)

        def search(
            self,
            raw_query: Any = None,
            by_properties: list[str] | None = None,
            by_dimensions: list[str] | None = None,
            by_identity: list[AnyHttpUrl] | list[str] | None = None,
        ) -> Generator[dict[str, Any]]:
            if raw_query is not None:
                raise MockBackendError(f"Raw queries are not supported by {self.__class__.__name__}.")

            results = []

            if by_properties:
                for entity in self._test_data:
                    if isinstance(entity.get("properties", {}), dict):
                        # SOFT7
                        if any(prop in entity["properties"] for prop in by_properties):
                            results.append(entity)
                    elif isinstance(entity.get("properties", []), list):
                        # SOFT5
                        if any(
                            requested_prop in (prop.get("name") for prop in entity["properties"])
                            for requested_prop in by_properties
                        ):
                            results.append(entity)
                    else:
                        raise MockBackendError("Invalid entity properties.")

            if by_dimensions:
                for entity in self._test_data:
                    if isinstance(entity.get("dimensions", {}), dict):
                        # SOFT7
                        if any(dim in entity["dimensions"] for dim in by_dimensions):
                            results.append(entity)
                    elif isinstance(entity.get("dimensions", []), list):
                        # SOFT5
                        if any(
                            requested_dim in (dim.get("name") for dim in entity["dimensions"])
                            for requested_dim in by_dimensions
                        ):
                            results.append(entity)
                    else:
                        raise MockBackendError("Invalid entity dimensions.")

            if by_identity:
                for identity in by_identity:
                    if identity in self.__test_data_uris:
                        results.append(self._test_data[self.__test_data_uris.index(identity)])

            yield from results

        def count(self, raw_query: Any = None) -> int:
            if raw_query is not None:
                raise MockBackendError(f"Raw queries are not supported by {self.__class__.__name__}.")

            return len(self.__test_data)

    monkeypatch.setattr("dataspaces_entities.backend.mongodb.MongoDBBackend", MockBackend)
