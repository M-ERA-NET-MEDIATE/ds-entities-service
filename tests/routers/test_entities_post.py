"""Test the service's /entities router with `POST` endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from ..conftest import ClientFixture, ParameterizeGetEntities


pytestmark = [
    pytest.mark.usefixtures("_empty_backend_collection", "_mock_openid_url_request"),
    pytest.mark.httpx_mock(assert_all_responses_were_requested=False),
]


ENDPOINT = "/entities"


def test_create_single_entity(
    client: ClientFixture,
    parameterized_entity: ParameterizeGetEntities,
) -> None:
    """Test creating a single entity."""
    import json

    # Create single entity
    with client(allowed_role="entities:write") as client_:
        response = client_.post(ENDPOINT, json=parameterized_entity.entity)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    # Check response
    assert response.status_code == 201, json.dumps(response_json, indent=2)
    assert isinstance(response_json, dict), json.dumps(response_json, indent=2)
    assert response_json == parameterized_entity.parsed_entity, json.dumps(response_json, indent=2)


def test_create_multiple_entities(
    static_dir: Path,
    client: ClientFixture,
) -> None:
    """Test creating multiple entities."""
    import json

    import yaml

    # Load entities
    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())
    scrubbed_entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "valid_entities_soft7.yaml").read_text()
    )

    # Create multiple entities
    with client(allowed_role="entities:write") as client_:
        response = client_.post(ENDPOINT, json=entities)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    # Check response
    assert response.status_code == 201, json.dumps(response_json, indent=2)
    assert isinstance(response_json, list), json.dumps(response_json, indent=2)
    assert response_json != entities, json.dumps(response_json, indent=2)
    assert response_json == scrubbed_entities, json.dumps(response_json, indent=2)


def test_create_no_entities(client: ClientFixture) -> None:
    """Test creating no entities."""
    # Create no entities
    with client(allowed_role="entities:write") as client_:
        response = client_.post(ENDPOINT, json=[])

    # Check response
    assert response.content == b"[]", response.content
    assert response.json() == [], response.json()
    assert response.status_code == 200, response.content


def test_create_invalid_entity(
    static_dir: Path,
    client: ClientFixture,
) -> None:
    """Test creating an invalid entity."""
    import json

    # Load invalid entities
    entities: list[dict[str, Any]] = [
        json.loads(invalid_entity_file.read_text())
        for invalid_entity_file in (static_dir / "invalid_entities").glob("*.json")
    ]

    # Create multiple invalid entities
    with client(raise_server_exceptions=False, allowed_role="entities:write") as client_:
        response = client_.post(ENDPOINT, json=entities)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    # Check response
    assert response.status_code == 422, json.dumps(response_json, indent=2)
    assert isinstance(response_json, dict), json.dumps(response_json, indent=2)
    assert "detail" in response_json, json.dumps(response_json, indent=2)

    # Create single invalid entities
    for entity in entities:
        identity = entity.get("uri", entity.get("identity", None)) or (
            f"{entity.get('namespace', '')}/{entity.get('version', '')}/{entity.get('name', '')}"
        )
        error_message = f"Failed to create entity with identity {identity}"

        with client(raise_server_exceptions=False, allowed_role="entities:write") as client_:
            response = client_.post(ENDPOINT, json=entity)

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            pytest.fail(f"Failed to decode response: {response.content!r}")

        # Check response
        assert response.status_code == 422, f"{error_message}\n{json.dumps(response_json, indent=2)}"
        assert isinstance(response_json, dict), f"{error_message}\n{json.dumps(response_json, indent=2)}"
        assert "detail" in response_json, f"{error_message}\n{json.dumps(response_json, indent=2)}"


@pytest.mark.skip_if_live_backend("Authentication is disabled in the live backend.")
def test_user_with_no_write_access(
    static_dir: Path,
    client: ClientFixture,
    live_backend: bool,
) -> None:
    """Test that a 403 Forbidden exception is raised if the user is a valid user, but does not have write
    access."""
    import json

    import yaml

    # Load entities
    entities = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())

    # Create single entity
    with client(allowed_role="entities:read") as client_:
        response = client_.post(ENDPOINT, json=entities)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    # Check response
    assert response.status_code == 403, json.dumps(response_json, indent=2)
    assert isinstance(response_json, dict), json.dumps(response_json, indent=2)
    assert "detail" in response_json, json.dumps(response_json, indent=2)
    assert "WWW-Authenticate" not in response.headers, response.headers

    if not live_backend:
        assert response_json["detail"] == "Unauthorized", json.dumps(response_json, indent=2)


@pytest.mark.skip_if_live_backend("Cannot mock write error in live backend.")
def test_backend_write_error_exception(
    static_dir: Path,
    client: ClientFixture,
) -> None:
    """Test that a 502 exception is raised if the backend cannot write the entity.

    This makes use of the customized `MockBackend` class to raise an exception when creating an entity that
    is not part of the `valid_entities.yaml` file.
    See `MockBackend.create` method in `tests/service/routers/conftest.py:_mock_backend()`.
    """
    import json

    import yaml

    valid_entity = {
        "identity": "http://onto-ns.com/meta/1.0/ValidEntity",
        "description": "A valid entity not in 'valid_entities.yaml'.",
        "dimensions": {},
        "properties": {
            "test": {
                "type": "string",
                "description": "Test property.",
            },
        },
    }

    # Load valid ("known") entities
    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())
    assert valid_entity not in entities, valid_entity

    # Create single entity
    with client(raise_server_exceptions=False, allowed_role="entities:write") as client_:
        response = client_.post(ENDPOINT, json=valid_entity)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    # Check response
    assert response.status_code == 502, json.dumps(response_json, indent=2)
    assert isinstance(response_json, dict), json.dumps(response_json, indent=2)
    assert "detail" in response_json, json.dumps(response_json, indent=2)
    assert response_json["detail"] == (
        f"Could not create entity with identity: {valid_entity['identity']}"
    ), json.dumps(response_json, indent=2)


@pytest.mark.skip_if_live_backend("Cannot mock create returns bad value in live backend.")
def test_backend_create_returns_bad_value(
    client: ClientFixture,
    parameterized_entity: ParameterizeGetEntities,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an exception is raised if the backend's create methods returns a bad
    value.

    Using the `parameterized_entity` fixture, to test the error response detail changes
    from the response checked in the `test_backend_write_error_exception` test.
    """
    # Monkeypatch the backend create method to return an unexpected value
    from entities_service.backend import mongodb as entities_backend

    monkeypatch.setattr(
        entities_backend.MongoDBBackend,
        "create",
        lambda *args, **kwargs: None,  # noqa: ARG005
    )

    # Create single entity
    with client(allowed_role="entities:write") as client_:
        response = client_.post(ENDPOINT, json=parameterized_entity.entity)

    response_json = response.json()

    # Check response
    assert response.status_code == 502, response_json
    assert isinstance(response_json, dict), response_json
    assert "detail" in response_json, response_json
    assert (
        response_json["detail"] == f"Could not create entity with identity: {parameterized_entity.identity}"
    ), response_json
