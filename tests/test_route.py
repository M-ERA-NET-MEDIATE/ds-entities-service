"""Test the service's only route to retrieve DLite/SOFT entities."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from tests.utils import parameterize_get_entities

if TYPE_CHECKING:
    from typing import Any

    from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("entity", "version", "name"),
    parameterize_get_entities(),
    ids=[f"{_.version}/{_.name}" for _ in parameterize_get_entities()],
)
def test_get_entity(
    entity: dict[str, Any],
    version: str,
    name: str,
    client: TestClient,
) -> None:
    """Test the route to retrieve a DLite/SOFT entity."""
    from fastapi import status

    with client as client:
        response = client.get(f"/{version}/{name}", timeout=5)

    assert (
        response.is_success
    ), f"Response: {response.json()}. Request: {response.request}"
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert (resolved_entity := response.json()) == entity, resolved_entity


@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="DLite-Python does not support Python3.12 and above.",
)
@pytest.mark.parametrize(
    ("entity", "version", "name"),
    parameterize_get_entities(),
    ids=[f"{_.version}/{_.name}" for _ in parameterize_get_entities()],
)
def test_get_entity_instance(
    entity: dict[str, Any],
    version: str,
    name: str,
    client: TestClient,
) -> None:
    """Validate that we can instantiate a DLite Instance from the response"""
    from dlite import Instance

    with client as client:
        response = client.get(f"/{version}/{name}", timeout=5)

    assert (resolve_entity := response.json()) == entity, resolve_entity

    Instance.from_dict(resolve_entity)


def test_get_entity_not_found(client: TestClient) -> None:
    """Test that the route returns a Not Found (404) for non existant URIs."""
    from fastapi import status

    version, name = "0.0", "NonExistantEntity"
    with client as client:
        response = client.get(f"/{version}/{name}", timeout=5)

    assert not response.is_success, "Non existant (valid) URI returned an OK response!"
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), f"Response:\n\n{response.json()}"


def test_get_entity_invalid_uri(client: TestClient) -> None:
    """Test that the service raises a pydantic ValidationError and returns an
    Unprocessable Entity (422) for invalid URIs.

    Test by reversing version and name in URI, thereby making it invalid.
    """
    from fastapi import status

    version, name = "1.0", "EntityName"
    with client as client:
        response = client.get(f"/{name}/{version}", timeout=5)

    assert not response.is_success, "Invalid URI returned an OK response!"
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), f"Response:\n\n{response.json()}"
