"""Utility functions for the entities service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from s7 import SOFT7Entity

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
        raise ValueError(
            "Entity must have either an identity/URI or all of 'namespace', 'version', and 'name' defined."
        )

    return f"{entity['namespace'].rstrip('/')}/{entity['version']}/{entity['name']}"
