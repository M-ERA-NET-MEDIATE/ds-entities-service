"""Test the service's /entities router with `POST` endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Literal

    from ...conftest import ClientFixture, MockAuthVerification, ParameterizeGetEntities


pytestmark = pytest.mark.usefixtures("_empty_backend_collection")


ENDPOINT = "/entities"


def test_create_single_entity(
    client: ClientFixture,
    parameterized_entity: ParameterizeGetEntities,
    mock_auth_verification: MockAuthVerification | None,
    auth_header: dict[Literal["Authorization"], str],
    live_backend: bool,
) -> None:
    """Test creating a single entity."""
    import json

    if not live_backend:
        # Setup mock responses for OAuth2 verification
        mock_auth_verification(auth_role="write")

    # Create single entity
    with client() as client_:
        response = client_.post(ENDPOINT, json=parameterized_entity.entity, headers=auth_header)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    # Check response
    assert response.status_code == 201, json.dumps(response_json, indent=2)
    assert isinstance(response_json, dict), json.dumps(response_json, indent=2)
    assert response_json == parameterized_entity.entity, json.dumps(response_json, indent=2)


def test_create_multiple_entities(
    static_dir: Path,
    client: ClientFixture,
    mock_auth_verification: MockAuthVerification,
    auth_header: dict[Literal["Authorization"], str],
) -> None:
    """Test creating multiple entities."""
    import yaml

    # Setup mock responses for OAuth2 verification
    mock_auth_verification(auth_role="write")

    # Load entities
    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())

    # Create multiple entities
    with client(auth_role="write") as client_:
        response = client_.post(
            ENDPOINT,
            json=entities,
            headers=auth_header,
        )

    response_json = response.json()

    # Check response
    assert response.status_code == 201, response_json
    assert isinstance(response_json, list), response_json
    assert response_json == entities, response_json


def test_create_no_entities(
    client: ClientFixture,
    mock_auth_verification: MockAuthVerification,
    auth_header: dict[Literal["Authorization"], str],
) -> None:
    """Test creating no entities."""
    from json import JSONDecodeError

    # Setup mock responses for OAuth2 verification
    mock_auth_verification(auth_role="write")

    # Create no entities
    with client(auth_role="write") as client_:
        response = client_.post(
            ENDPOINT,
            json=[],
            headers=auth_header,
        )

    # Check response
    assert response.content == b"", response.content
    assert response.status_code == 204, response.content

    with pytest.raises(JSONDecodeError):
        response.json()


def test_create_invalid_entity(
    static_dir: Path,
    client: ClientFixture,
    mock_auth_verification: MockAuthVerification,
    auth_header: dict[Literal["Authorization"], str],
) -> None:
    """Test creating an invalid entity."""
    import json

    # Setup mock responses for OAuth2 verification
    mock_auth_verification(auth_role="write")

    # Load invalid entities
    entities: list[dict[str, Any]] = [
        json.loads(invalid_entity_file.read_text())
        for invalid_entity_file in (static_dir / "invalid_entities").glob("*.json")
    ]

    # Create multiple invalid entities
    with client(auth_role="write", raise_server_exceptions=False) as client_:
        response = client_.post(
            ENDPOINT,
            json=entities,
            headers=auth_header,
        )

    response_json = response.json()

    # Check response
    assert response.status_code == 422, response_json
    assert isinstance(response_json, dict), response_json
    assert "detail" in response_json, response_json

    # Create single invalid entities
    for entity in entities:
        uri = entity.get("uri", None) or (
            f"{entity.get('namespace', '')}/{entity.get('version', '')}/{entity.get('name', '')}"
        )
        error_message = f"Failed to create entity with uri {uri}"

        with client(auth_role="write", raise_server_exceptions=False) as client_:
            response = client_.post(
                ENDPOINT,
                json=entity,
                headers=auth_header,
            )

        response_json = response.json()

        # Check response
        assert response.status_code == 422, f"{error_message}\n{response_json}"
        assert isinstance(response_json, dict), f"{error_message}\n{response_json}"
        assert "detail" in response_json, f"{error_message}\n{response_json}"


def test_user_with_no_write_access(
    static_dir: Path,
    client: ClientFixture,
    mock_auth_verification: MockAuthVerification,
    auth_header: dict[Literal["Authorization"], str],
) -> None:
    """Test that a 401 exception is raised if the user does not have write access."""
    import yaml

    # Setup mock responses for OAuth2 verification
    mock_auth_verification(auth_role="read")

    # Load entities
    entities = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())

    # Create single entity
    with client(auth_role="read") as client_:
        response = client_.post(
            ENDPOINT,
            json=entities,
            headers=auth_header,
        )

    response_json = response.json()

    # Check response
    assert response.status_code == 403, response_json
    assert isinstance(response_json, dict), response_json
    assert "detail" in response_json, response_json
    assert response_json["detail"] == (
        "You do not have the rights to create entities. "
        "Please contact the ds-entities-service group maintainer."
    ), response_json
    assert "WWW-Authenticate" in response.headers, response.headers
    assert response.headers["WWW-Authenticate"] == "Bearer", response.headers["WWW-Authenticate"]


def test_backend_write_error_exception(
    static_dir: Path,
    client: ClientFixture,
    mock_auth_verification: MockAuthVerification,
    auth_header: dict[Literal["Authorization"], str],
) -> None:
    """Test that a 502 exception is raised if the backend cannot write the entity."""
    import yaml

    # Setup mock responses for OAuth2 verification
    mock_auth_verification(auth_role="write")

    valid_entity = {
        "uri": "http://onto-ns.com/meta/1.0/ValidEntity",
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
    with client(auth_role="write", raise_server_exceptions=False) as client_:
        response = client_.post(
            ENDPOINT,
            json=valid_entity,
            headers=auth_header,
        )

    response_json = response.json()

    # Check response
    assert response.status_code == 502, response_json
    assert isinstance(response_json, dict), response_json
    assert "detail" in response_json, response_json
    assert response_json["detail"] == (
        f"Could not create entity with uri: {valid_entity['uri']}"
    ), response_json


def test_backend_create_returns_bad_value(
    client: ClientFixture,
    parameterized_entity: ParameterizeGetEntities,
    mock_auth_verification: MockAuthVerification,
    auth_header: dict[Literal["Authorization"], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an exception is raised if the backend's create methods returns a bad
    value.

    Using the `parameterized_entity` fixture, to test the error response detail changes
    from the response checked in the `test_backend_write_error_exception` test.
    """
    # Monkeypatch the backend create method to return an unexpected value
    from entities_service.service.backend import mongodb as entities_backend

    monkeypatch.setattr(
        entities_backend.MongoDBBackend,
        "create",
        lambda *args, **kwargs: None,  # noqa: ARG005
    )

    # Setup mock responses for OAuth2 verification
    mock_auth_verification(auth_role="write")

    # Create single entity
    with client(auth_role="write") as client_:
        response = client_.post(
            ENDPOINT,
            json=parameterized_entity.entity,
            headers=auth_header,
        )

    response_json = response.json()

    # Check response
    assert response.status_code == 502, response_json
    assert isinstance(response_json, dict), response_json
    assert "detail" in response_json, response_json
    assert (
        response_json["detail"] == f"Could not create entity with uri: {parameterized_entity.uri}"
    ), response_json
