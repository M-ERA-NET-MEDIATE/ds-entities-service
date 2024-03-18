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
    import json

    from fastapi import status

    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [parameterized_entity.uri]}, timeout=5)

    try:
        resolved_entity = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert (
        response.is_success
    ), f"Response: {json.dumps(resolved_entity, indent=2)}. Request: {response.request}"
    assert response.status_code == status.HTTP_200_OK, json.dumps(resolved_entity, indent=2)

    assert resolved_entity == parameterized_entity.entity, json.dumps(resolved_entity, indent=2)


@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="DLite-Python does not support Python 3.12+.",
)
def test_get_entity_instance(
    parameterized_entity: ParameterizeGetEntities,
    client: ClientFixture,
) -> None:
    """Validate that we can instantiate a DLite Instance from the response"""
    import json

    from dlite import Instance

    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [parameterized_entity.uri]}, timeout=5)

    try:
        resolved_entity = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert resolved_entity == parameterized_entity.entity, resolved_entity

    Instance.from_dict(resolved_entity)


def test_get_entity_not_found(client: ClientFixture) -> None:
    """Test that the route returns a Not Found (404) for non existent URIs."""
    import json

    from fastapi import status

    namespace, version, name = "http://onto-ns.com/meta", "0.0", "NonExistentEntity"
    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [f"{namespace}/{version}/{name}"]}, timeout=5)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert not response.is_success, "Non existent (valid) URI returned an OK response!"
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), f"Response:\n{json.dumps(response_json, indent=2)}"


def test_get_entity_invalid_uri(client: ClientFixture) -> None:
    """Test that the service raises a pydantic ValidationError and returns an
    Unprocessable Entity (422) for invalid URIs.

    Test by reversing version and name in URI, thereby making it invalid.
    """
    import json

    from fastapi import status

    namespace, version, name = "http://onto-ns.com/meta", "1.0", "EntityName"
    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [f"{namespace}/{name}/{version}"]}, timeout=5)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert not response.is_success, "Invalid URI returned an OK response!"
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), f"Response:\n{json.dumps(response_json, indent=2)}"
