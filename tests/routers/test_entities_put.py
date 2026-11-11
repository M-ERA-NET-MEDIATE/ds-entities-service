"""Test the service's /entities router with `PUT` endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from ..conftest import ClientFixture


pytestmark = [
    pytest.mark.usefixtures("_mock_openid_url_request"),
    pytest.mark.httpx2_mock(assert_all_responses_were_requested=False),
]


ENDPOINT = "/entities"


@pytest.mark.parametrize("backend_test_data", [[]], ids=["empty_backend"])
def test_put_create_multiple_entities(
    static_dir: Path,
    client: ClientFixture,
) -> None:
    """Test creating multiple new entities with PUT (a list response)."""
    import json

    import yaml

    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())
    scrubbed_entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "valid_entities_soft7.yaml").read_text()
    )

    with client(allowed_role="entities:edit") as client_:
        response = client_.put(ENDPOINT, json=entities)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        pytest.fail(f"Failed to decode response: {response.content!r}")

    assert response.status_code == 201, json.dumps(response_json, indent=2)
    assert isinstance(response_json, list), json.dumps(response_json, indent=2)
    assert response_json == scrubbed_entities, json.dumps(response_json, indent=2)


def test_put_replace_existing_entities(
    static_dir: Path,
    client: ClientFixture,
) -> None:
    """Test replacing multiple existing entities with PUT (no content response)."""
    import yaml

    # The backend is pre-filled with these entities
    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())

    with client(allowed_role="entities:edit") as client_:
        response = client_.put(ENDPOINT, json=entities)

    assert response.status_code == 204, response.content
    assert not response.content, response.content
