"""Utility functions for the entities service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from s7 import SOFT7Entity

from dataspaces_entities.exceptions import InvalidEntityError

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


def get_identity(entity: SOFT7Entity | dict[str, Any]) -> str:
    """Get the identity of an entity."""
    if isinstance(entity, SOFT7Entity):
        return str(entity.identity)

    if not isinstance(entity, dict):
        raise TypeError("entity must be a SOFT7Entity or a dictionary.")

    if "uri" in entity:
        return entity["uri"]

    if "identity" in entity:
        return entity["identity"]

    if not all(
        (key in entity and isinstance(entity[key], str)) for key in ("namespace", "version", "name")
    ):
        raise InvalidEntityError(
            "Entity must have either an identity/URI or all of 'namespace', 'version', and 'name' defined."
        )

    return f"{entity['namespace'].rstrip('/')}/{entity['version']}/{entity['name']}"


def generate_error_display_ids(
    entities: list[SOFT7Entity | dict[str, Any]] | None = None,
    entity_ids: list[str] | None = None,
) -> list[str]:
    """Generate a list of entity identities for error display.

    Limits the number of displayed identities based on configuration.
    """
    from dataspaces_entities.config import get_config

    if entities is None and entity_ids is None:
        raise ValueError("At least one of 'entities' or 'entity_ids' must be provided.")

    max_entities_in_errors = get_config().max_entities_in_errors

    entity_ids = entity_ids or []

    if entities is not None:
        entity_ids.extend([get_identity(entity) for entity in entities])

    # Remove duplicates, we don't care about order
    entity_ids = list(set(entity_ids))

    display_ids = entity_ids[:max_entities_in_errors]
    remaining_count = len(entity_ids) - max_entities_in_errors
    if remaining_count > 0:
        display_ids.append(f"... and {remaining_count} more")

    return display_ids
