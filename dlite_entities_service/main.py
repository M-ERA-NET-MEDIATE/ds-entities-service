"""The main application module."""
from pathlib import Path as sysPath
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Path, status

from dlite_entities_service import __version__
from dlite_entities_service.backend import ENTITIES_COLLECTION
from dlite_entities_service.config import CONFIG
from dlite_entities_service.logger import LOGGER
from dlite_entities_service.models import Entity

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


APP = FastAPI(
    title="DLite Entities Service",
    version=__version__,
    description=(
        sysPath(__file__).resolve().parent.parent.resolve() / "README.md"
    ).read_text(encoding="utf8"),
)

SEMVER_REGEX = (
    r"^(?P<major>0|[1-9]\d*)(?:\.(?P<minor>0|[1-9]\d*))?(?:\.(?P<patch>0|[1-9]\d*))?"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
"""Semantic Versioning regular expression.

Slightly changed version of the one found at https://semver.org.
The changed bits pertain to `minor` and `patch`, which are now both optional.
"""


@APP.get(
    "/{version}/{name}",
    response_model=Entity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
)
async def get_entity(
    version: str = Path(
        ...,
        regex=SEMVER_REGEX,
        description="The version part must be of the kind MAJOR.MINOR.",
    ),
    name: str = Path(
        ...,
        regex=r"^[A-Za-z]+$",
        description="The name part must be CamelCase without any white space.",
    ),
) -> "dict[str, Any]":
    """Get a DLite entity."""
    query = {
        "$or": [
            {"version": version, "name": name},
            {"uri": f"{CONFIG.base_url}/{version}/{name}"},
        ]
    }
    LOGGER.debug("Performing MongoDB query: %r", query)
    entity_doc: "dict[str, Any]" = ENTITIES_COLLECTION.find_one(query)
    if entity_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find entity: uri={CONFIG.base_url}/{version}/{name}",
        )
    LOGGER.debug("Found entity's MongoDB ID: %s", entity_doc["_id"])
    entity_doc.pop("_id", None)
    return entity_doc


@APP.on_event("startup")
async def on_startup() -> None:
    """Do some logging."""
    LOGGER.debug("Starting service with config: %s", CONFIG)
