"""The main application module."""
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Path, status

from dlite_entities_service import __version__
from dlite_entities_service.backend import ENTITIES_COLLECTION
from dlite_entities_service.config import CONFIG
from dlite_entities_service.models import Entity

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


APP = FastAPI(
    title="DLite Entities Service",
    version=__version__,
    description="REPLACE WITH README.md",
)


@APP.get(
    "/{version}/{name}",
    response_model=Entity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
)
async def get_entity(
    version: str = Path(
        ...,
        regex=r"^[0-9]+\.[0-9]+$",
        description="The version part must be of the kind MAJOR.MINOR.",
    ),
    name: str = Path(
        ...,
        regex=r"^([A-Z][a-z]+)+$",
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
    entity_doc: "dict[str, Any]" = ENTITIES_COLLECTION.find_one(query)
    if entity_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find entity: uri={CONFIG.base_url}/{version}/{name}",
        )
    entity_doc.pop("_id", None)
    return entity_doc
