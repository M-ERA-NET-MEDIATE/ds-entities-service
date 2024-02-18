"""Test the service's /entities router with `GET` endpoints."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ...conftest import ClientFixture, ParameterizeGetEntities


ENDPOINT = "/entities"


def test_get_entity(
    parameterized_entity: ParameterizeGetEntities,
    client: ClientFixture,
) -> None:
    """Test the route to retrieve an entity."""
    from fastapi import status

    with client() as client_:
        response = client_.get(f"{ENDPOINT}/{parameterized_entity.uri}", timeout=5)

    assert (
        response.is_success
    ), f"Response: {response.json()}. Request: {response.request}"
    assert response.status_code == status.HTTP_200_OK, response.json()

    resolved_entity = response.json()
    assert resolved_entity == parameterized_entity.entity, resolved_entity


@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="DLite-Python does not support Python3.12 and above.",
)
def test_get_entity_instance(
    parameterized_entity: ParameterizeGetEntities,
    client: ClientFixture,
) -> None:
    """Validate that we can instantiate a DLite Instance from the response"""
    from dlite import Instance

    with client() as client_:
        response = client_.get(f"{ENDPOINT}/{parameterized_entity.uri}", timeout=5)

    resolved_entity = response.json()
    assert resolved_entity == parameterized_entity.entity, resolved_entity

    Instance.from_dict(resolved_entity)


def test_get_entity_not_found(client: ClientFixture) -> None:
    """Test that the route returns a Not Found (404) for non existant URIs."""
    from fastapi import status

    namespace, version, name = "http://onto-ns.com/meta", "0.0", "NonExistantEntity"
    with client() as client_:
        response = client_.get(f"{ENDPOINT}/{namespace}/{version}/{name}", timeout=5)

    assert not response.is_success, "Non existant (valid) URI returned an OK response!"
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), f"Response:\n\n{response.json()}"


def test_get_entity_invalid_uri(client: ClientFixture) -> None:
    """Test that the service raises a pydantic ValidationError and returns an
    Unprocessable Entity (422) for invalid URIs.

    Test by reversing version and name in URI, thereby making it invalid.
    """
    from fastapi import status

    namespace, version, name = "http://onto-ns.com/meta", "1.0", "EntityName"
    with client() as client_:
        response = client_.get(f"{ENDPOINT}/{namespace}/{name}/{version}", timeout=5)

    assert not response.is_success, "Invalid URI returned an OK response!"
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), f"Response:\n\n{response.json()}"
