"""Test the MongoDB backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ..conftest import ParameterizeGetEntities


pytestmark = pytest.mark.skip_if_not_live_backend(reason="Tests are only valid with a live backend.")


def test_multiple_initialize() -> None:
    """Test initializing the backend multiple times.

    At this point, the backend should already have been initialized once,
    so the second time should not create any new indices.
    """
    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    # Check current indices
    indices = backend._collection.index_information()
    assert len(indices) == 2, indices
    assert "IDENTITY" in indices
    assert "_id_" in indices

    # Initialize the backend again, ensuring the "IDENTITY" index is not recreated
    backend.initialize()

    indices = backend._collection.index_information()
    assert len(indices) == 2, indices
    assert "IDENTITY" in indices
    assert "_id_" in indices


def test_close() -> None:
    """Test closing the backend.

    Note, this doesn't actually do anything for the MongoDB backend at this point.
    """
    from dataspaces_entities.backend import get_backend

    get_backend().close()


@pytest.mark.usefixtures("_empty_backend_collection")
def test_create(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the create method."""
    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    # Create a single entity
    entity_from_backend = backend.create([parameterized_entity.parsed_entity])

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend == parameterized_entity.parsed_entity

    # Create multiple entities
    raw_entities = [
        {
            "identity": "http://onto-ns.com/meta/1.0/Test",
            "properties": {
                "test": {
                    "type": "string",
                    "description": "test",
                }
            },
        },
        {
            "identity": "http://onto-ns.com/meta/1.0/AnotherTest",
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


def test_read(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the read method."""
    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    entity_from_backend = backend.read(parameterized_entity.identity)

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend == parameterized_entity.parsed_entity


def test_update(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the update method."""
    from copy import deepcopy

    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, parse_identity

    from dataspaces_entities.backend import get_backend

    backend = get_backend()

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

    namespace, version, name = parse_identity(SOFT7IdentityURI(parameterized_entity.identity))

    # Retrieve the entity again
    entity_from_backend = backend._collection.find_one(
        {
            "$or": [
                {"namespace": str(namespace), "version": version, "name": name},
                {"identity": parameterized_entity.identity},
            ]
        },
        projection={"_id": False},
    )

    assert isinstance(entity_from_backend, dict)
    assert entity_from_backend != parameterized_entity.parsed_entity
    assert entity_from_backend == changed_raw_entity


def test_delete(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the delete method."""

    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, parse_identity

    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    namespace, version, name = parse_identity(SOFT7IdentityURI(parameterized_entity.identity))

    # Ensure the entity currently exists in the backend
    entity_from_backend = backend._collection.find_one(
        {
            "$or": [
                {"namespace": str(namespace), "version": version, "name": name},
                {"identity": parameterized_entity.identity},
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
                {"namespace": str(namespace), "version": version, "name": name},
                {"identity": parameterized_entity.identity},
            ]
        },
        projection={"_id": False},
    )

    assert entity_from_backend is None
    assert len(backend) == number_of_entities - 1


def test_search(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the search method.

    Note, this method only accepts valid MongoDB queries.
    """
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, parse_identity

    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    namespace, version, name = parse_identity(SOFT7IdentityURI(parameterized_entity.identity))

    # Search for the entity
    entities_from_backend = list(
        backend.search(
            {
                "$or": [
                    {"namespace": str(namespace), "version": version, "name": name},
                    {"identity": parameterized_entity.identity},
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


def test_count(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the count method."""
    from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, parse_identity

    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    # Count all entities
    number_of_entities = len(backend)
    assert backend.count({}) == number_of_entities

    namespace, version, name = parse_identity(SOFT7IdentityURI(parameterized_entity.identity))

    # Count the entity
    assert (
        backend.count(
            {
                "$or": [
                    {"namespace": str(namespace), "version": version, "name": name},
                    {"identity": parameterized_entity.identity},
                ]
            }
        )
        == 1
    )


def test_contains(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the magic method __contains__."""
    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    assert 42 not in backend

    assert parameterized_entity.identity in backend
    assert parameterized_entity.entity in backend


def test_iter(parameterized_entity: ParameterizeGetEntities) -> None:
    """Test the magic method: __iter__."""
    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    entities = list(backend)
    assert parameterized_entity.parsed_entity in entities

    assert len(entities) == backend._collection.count_documents({})


def test_len() -> None:
    """Test the magic method: __len__."""
    from dataspaces_entities.backend import get_backend

    backend = get_backend()

    number_of_entities = backend._collection.count_documents({})

    assert len(backend) == number_of_entities
