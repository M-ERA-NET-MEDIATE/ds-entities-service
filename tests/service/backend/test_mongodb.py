"""Test the MongoDB backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Literal, Protocol

    from entities_service.service.backend.mongodb import MongoDBBackend

    from ...conftest import GetBackendUserFixture, ParameterizeGetEntities

    class GetMongoBackend(Protocol):
        """Get the MongoDB backend."""

        def __call__(self, auth: Literal["read", "write"] | None = None) -> MongoDBBackend: ...


pytestmark = pytest.mark.skip_if_not_live_backend(reason="Tests are only valid with a live backend.")


@pytest.fixture()
def mongo_backend(get_backend_user: GetBackendUserFixture) -> GetMongoBackend:
    """Get a MongoDB backend."""

    def _mongo_backend(auth: Literal["read", "write"] | None = None) -> MongoDBBackend:
        from entities_service.service.backend import get_backend

        backend_user = get_backend_user(auth)

        return get_backend(
            auth_level=auth,
            settings={
                "mongo_username": backend_user["username"],
                "mongo_password": backend_user["password"],
            },
        )

    return _mongo_backend


def test_multiple_initialize(mongo_backend: GetMongoBackend) -> None:
    """Test initializing the backend multiple times.

    At this point, the backend should already have been initialized once,
    so the second time should not create any new indices.
    """
    backend = mongo_backend("write")

    # Check current indices
    indices = backend._collection.index_information()
    assert len(indices) == 2, indices
    assert "URI" in indices
    assert "_id_" in indices

    # Initialize the backend again, ensuring the "URI" index is not recreated
    backend.initialize()

    indices = backend._collection.index_information()
    assert len(indices) == 2, indices
    assert "URI" in indices
    assert "_id_" in indices


def test_close() -> None:
    """Test closing the backend."""
    from entities_service.service.backend import get_backend
    from entities_service.service.backend.mongodb import (
        MONGO_CLIENTS,
    )

    original_number_of_clients = 2

    assert MONGO_CLIENTS is not None
    assert len(MONGO_CLIENTS) == original_number_of_clients
    assert "read" in MONGO_CLIENTS
    assert "write" in MONGO_CLIENTS

    get_backend().close()

    # The clients are never _actually_ close
    assert len(MONGO_CLIENTS) == original_number_of_clients
    assert "read" in MONGO_CLIENTS
    assert "write" in MONGO_CLIENTS


@pytest.mark.usefixtures("_empty_backend_collection")
def test_create(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the create method."""
    backend = mongo_backend("write")

    # Create a single entity
    entity_from_backend = backend.create([parameterized_entity.parsed_entity])

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend == parameterized_entity.parsed_entity

    # Create multiple entities
    raw_entities = [
        {
            "uri": "http://onto-ns.com/meta/1.0/Test",
            "properties": {
                "test": {
                    "type": "string",
                    "description": "test",
                }
            },
        },
        {
            "uri": "http://onto-ns.com/meta/1.0/AnotherTest",
            "properties": {
                "test": {
                    "type": "string",
                    "description": "another test",
                }
            },
        },
    ]

    assert parameterized_entity.parsed_entity not in raw_entities

    entities_from_backend = backend.create(raw_entities)

    assert isinstance(entities_from_backend, list)
    assert len(entities_from_backend) == 2
    assert entities_from_backend[0] in raw_entities
    assert entities_from_backend[1] in raw_entities


def test_read(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the read method."""
    backend = mongo_backend("read")

    entity_from_backend = backend.read(parameterized_entity.identity)

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend == parameterized_entity.parsed_entity


def test_update(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the update method."""
    from copy import deepcopy

    from entities_service.service.backend.mongodb import URI_REGEX

    backend = mongo_backend("write")

    # Change current entity
    changed_raw_entity = deepcopy(parameterized_entity.parsed_entity)

    if isinstance(changed_raw_entity["properties"], dict):
        assert "test" not in changed_raw_entity["properties"]
        changed_raw_entity["properties"]["test"] = {
            "type": "string",
            "description": "test",
        }
    elif isinstance(changed_raw_entity["properties"], list):
        assert all(_["name"] != "test" for _ in changed_raw_entity["properties"])
        changed_raw_entity["properties"].append(
            {
                "name": "test",
                "type": "string",
                "description": "test",
            }
        )
    else:
        pytest.fail("Unknown properties type / entity format")

    # Apply the change
    backend.update(parameterized_entity.identity, changed_raw_entity)

    # Retrieve the entity again
    entity_from_backend = backend._collection.find_one(
        {
            "$or": [
                URI_REGEX.match(parameterized_entity.identity).groupdict(),
                {"uri": parameterized_entity.identity},
            ]
        },
        projection={"_id": False},
    )

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend != parameterized_entity.parsed_entity
    assert entity_from_backend == changed_raw_entity


def test_delete(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the delete method."""
    from entities_service.service.backend.mongodb import URI_REGEX

    backend = mongo_backend("write")

    # Ensure the entity currently exists in the backend
    entity_from_backend = backend._collection.find_one(
        {
            "$or": [
                URI_REGEX.match(parameterized_entity.identity).groupdict(),
                {"uri": parameterized_entity.identity},
            ]
        },
        projection={"_id": False},
    )

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend == parameterized_entity.parsed_entity

    # Check the current number of entities
    number_of_entities = len(backend)

    # Delete the entity
    backend.delete([parameterized_entity.identity])

    # Check that the entity is gone
    entity_from_backend = backend._collection.find_one(
        {
            "$or": [
                URI_REGEX.match(parameterized_entity.identity).groupdict(),
                {"uri": parameterized_entity.identity},
            ]
        },
        projection={"_id": False},
    )

    assert entity_from_backend is None
    assert len(backend) == number_of_entities - 1


def test_search(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the search method.

    Note, this method only accepts valid MongoDB queries.
    """
    from entities_service.service.backend.mongodb import URI_REGEX

    backend = mongo_backend("read")

    # Search for the entity
    entities_from_backend = list(
        backend.search(
            {
                "$or": [
                    URI_REGEX.match(parameterized_entity.identity).groupdict(),
                    {"uri": parameterized_entity.identity},
                ]
            }
        )
    )

    assert len(entities_from_backend) == 1
    assert entities_from_backend[0] == parameterized_entity.parsed_entity

    # Search for all entities
    number_of_entities = len(backend)
    entities_from_backend = list(backend.search({}))

    assert len(entities_from_backend) == number_of_entities
    assert all(isinstance(_, dict) for _ in entities_from_backend)
    assert parameterized_entity.parsed_entity in entities_from_backend


def test_count(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the count method."""
    from entities_service.service.backend.mongodb import URI_REGEX

    backend = mongo_backend("read")

    # Count all entities
    number_of_entities = len(backend)
    assert backend.count({}) == number_of_entities

    # Count the entity
    assert (
        backend.count(
            {
                "$or": [
                    URI_REGEX.match(parameterized_entity.identity).groupdict(),
                    {"uri": parameterized_entity.identity},
                ]
            }
        )
        == 1
    )


def test_contains(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the magic method __contains__."""
    backend = mongo_backend("read")

    assert 42 not in backend

    assert parameterized_entity.identity in backend
    assert parameterized_entity.entity in backend


def test_iter(mongo_backend: GetMongoBackend, parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the magic method: __iter__."""
    backend = mongo_backend("read")

    entities = list(backend)
    assert parameterized_entity.parsed_entity in entities

    assert len(entities) == backend._collection.count_documents({})


def test_len(mongo_backend: GetMongoBackend) -> None:
    """Test the magic method: __len__."""
    backend = mongo_backend("read")

    number_of_entities = backend._collection.count_documents({})

    assert len(backend) == number_of_entities
