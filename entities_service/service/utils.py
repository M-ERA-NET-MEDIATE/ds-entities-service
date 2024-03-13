"""Utility functions for the entities service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from entities_service.models import SOFTModelTypes
from entities_service.models import get_uri as get_uri_from_model

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from entities_service.models import VersionedSOFTEntity


def get_uri(entity: VersionedSOFTEntity | dict[str, Any]) -> str:
    """Get the URI of an entity."""
    if isinstance(entity, SOFTModelTypes):
        return get_uri_from_model(entity)

    if not isinstance(entity, dict):
        raise TypeError("Entity must be a SOFTModelType or a dictionary.")

    if "uri" in entity:
        return entity["uri"]

    if not all(
        (key in entity and isinstance(entity[key], str))
        for key in ("namespace", "version", "name")
    ):
        raise ValueError(
            "Entity must have either a URI or all of namespace, version, and name "
            "defined."
        )

    return f"{entity['namespace'].rstrip('/')}/{entity['version']}/{entity['name']}"
