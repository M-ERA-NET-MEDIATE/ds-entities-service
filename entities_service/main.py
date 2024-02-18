"""The main application module."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path as sysPath
from typing import TYPE_CHECKING

from fastapi import FastAPI

from entities_service import __version__
from entities_service.service.backend import get_backend
from entities_service.service.config import CONFIG
from entities_service.service.logger import setup_logger
from entities_service.service.routers import get_routers

if TYPE_CHECKING:  # pragma: no cover
    pass


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
    title="Entities Service for DataSpaces",
    version=__version__,
    description="A service for managing entities in DataSpaces.",
    lifespan=lifespan,
)

# Add routers
for router in get_routers():
    APP.include_router(router)
