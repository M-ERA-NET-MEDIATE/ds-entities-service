"""Utility functions for tests."""
from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from typing import Any


class ParameterizeGetEntities(NamedTuple):
    """Returned tuple from parameterizing all entities."""

    entity: dict[str, Any]
    version: str
    name: str


def get_version_name(uri: str) -> tuple[str, str]:
    """Return the version and name part of a uri."""
    import re

    from dlite_entities_service.service.config import CONFIG

    namespace = str(CONFIG.base_url).rstrip("/")

    match = re.match(
        rf"^{re.escape(namespace)}/(?P<version>[^/]+)/(?P<name>[^/]+)$", uri
    )
    assert match is not None, (
        f"Could not retrieve version and name from {uri!r}. "
        "URI must be of the form: "
        f"{namespace}/{{version}}/{{name}}\n\n"
        "Hint: Did you (inadvertently) set the base_url to something?"
    )

    return match.group("version") or "", match.group("name") or ""


def get_uri(entity: dict[str, Any]) -> str:
    """Return the uri for an entity."""
    namespace = entity.get("namespace")
    version = entity.get("version")
    name = entity.get("name")

    assert not any(
        _ is None for _ in (namespace, version, name)
    ), "Could not retrieve namespace, version, and/or name from test entities."

    return f"{namespace}/{version}/{name}"


def parameterize_get_entities() -> list[ParameterizeGetEntities]:
    """Parameterize the test to retrieve all entities."""
    from pathlib import Path

    import yaml

    static_dir = (Path(__file__).parent / "static").resolve()

    results: list[ParameterizeGetEntities] = []

    entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "entities.yaml").read_text()
    )

    for entity in entities:
        uri = entity.get("uri") or get_uri(entity)

        version, name = get_version_name(uri)

        results.append(ParameterizeGetEntities(entity, version, name))

    return results
