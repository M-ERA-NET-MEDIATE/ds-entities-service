"""Test the service's /entities router with `GET` endpoints."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ..conftest import ClientFixture, ParameterizeGetEntities

pytestmark = [
    pytest.mark.usefixtures("_mock_openid_url_request"),
    pytest.mark.httpx_mock(assert_all_responses_were_requested=False),
]

ENDPOINT = "/entities"


def test_get_entity(
    parameterized_entity: ParameterizeGetEntities,
    client: ClientFixture,
) -> None:
    """Test the route to retrieve an entity."""
    import json

    from fastapi import status

    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [parameterized_entity.identity]})

    try:
        resolved_entity = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert (
        response.is_success
    ), f"Response: {json.dumps(resolved_entity, indent=2)}. Request: {response.request}"
    assert response.status_code == status.HTTP_200_OK, json.dumps(resolved_entity, indent=2)

    assert resolved_entity == parameterized_entity.parsed_entity, json.dumps(resolved_entity, indent=2)


@pytest.mark.skipif(sys.version_info >= (3, 13), reason="DLite does not support Python 3.13+")
def test_get_entity_instance(
    parameterized_entity: ParameterizeGetEntities,
    client: ClientFixture,
) -> None:
    """Validate that we can instantiate a DLite Instance from the response"""
    import json

    from dlite import Instance

    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [parameterized_entity.identity]})

    try:
        resolved_entity = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert resolved_entity == parameterized_entity.parsed_entity, resolved_entity

    # Tweak resolved entity to be DLite compatible
    resolved_entity["uri"] = resolved_entity.pop("identity")
    for property_name, property_value in list(resolved_entity["properties"].items()):
        if property_value["type"].startswith("http"):
            resolved_entity["properties"][property_name]["$ref"] = property_value["type"]
            resolved_entity["properties"][property_name]["type"] = "ref"

    Instance.from_dict(resolved_entity)


def test_get_entity_not_found(client: ClientFixture) -> None:
    """Test that the route returns a Not Found (404) for non existent identities."""
    import json

    from fastapi import status

    namespace, version, name = "http://onto-ns.com/meta", "0.0", "NonExistentEntity"
    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [f"{namespace}/{version}/{name}"]})

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert not response.is_success, "Non existent (valid) identity returned an OK response!"
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), f"Response:\n{json.dumps(response_json, indent=2)}"


def test_get_entity_invalid_identity(client: ClientFixture) -> None:
    """Test that the service raises a pydantic ValidationError and returns an
    Unprocessable Entity (422) for invalid identities.

    Test by reversing version and name in identity, thereby making it invalid.
    """
    import json

    from fastapi import status

    namespace, version, name = "http://onto-ns.com/meta", "1.0", "EntityName"
    with client() as client_:
        response = client_.get(ENDPOINT, params={"id": [f"{namespace}/{name}/{version}"]})

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Response not JSON: {response.text}")

    assert not response.is_success, "Invalid identity returned an OK response!"
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), f"Response:\n{json.dumps(response_json, indent=2)}"
