"""The main application module."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path as sysPath
from typing import TYPE_CHECKING, Annotated

from fastapi import FastAPI, HTTPException, Path, status

from entities_service import __version__
from entities_service.models import VersionedSOFTEntity
from entities_service.service.backend import get_backend
from entities_service.service.config import CONFIG
from entities_service.service.logger import setup_logger
from entities_service.service.routers import get_routers

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


LOGGER = logging.getLogger("entities_service")


# Application lifespan function
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Add lifespan events to the application."""
    # Initialize logger
    setup_logger()

    LOGGER.debug("Starting service with config: %s", CONFIG)

    # Initialize backend
    get_backend(CONFIG.backend, auth_level="write").initialize()

    # Run application
    yield


# Setup application
APP = FastAPI(
    title="Entities Service",
    version=__version__,
    description=(
        sysPath(__file__).resolve().parent.parent.resolve() / "README.md"
    ).read_text(encoding="utf8"),
    lifespan=lifespan,
    root_path=CONFIG.base_url.path if CONFIG.base_url.path != "/" else "",
)

# Add routers
for router in get_routers():
    APP.include_router(router)


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
    response_model=VersionedSOFTEntity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
)
async def get_entity(
    version: Annotated[
        str,
        Path(
            title="Entity version",
            pattern=SEMVER_REGEX,
            description=(
                "The version part must be a semantic version, following the schema "
                "laid out by SemVer.org."
            ),
        ),
    ],
    name: Annotated[
        str,
        Path(
            title="Entity name",
            pattern=r"(?i)^[A-Z]+$",
            description=(
                "The name part is without any white space. It is conventionally "
                "written in PascalCase."
            ),
        ),
    ],
) -> dict[str, Any]:
    """Get an entity."""
    uri = f"{str(CONFIG.base_url).rstrip('/')}/{version}/{name}"
    entity = get_backend().read(uri)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find entity: uri={uri}",
        )
    return entity
