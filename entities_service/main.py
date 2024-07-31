"""The main application module."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from entities_service import __version__
from entities_service.service.backend import get_backend
from entities_service.service.config import CONFIG
from entities_service.service.logger import setup_logger
from entities_service.service.routers import get_routers
from entities_service.service.security import SECURITY_SCHEME

LOGGER = logging.getLogger("entities_service")


# Application lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Add lifespan events to the application."""
    # Initialize logger
    setup_logger()

    LOGGER.debug("Starting service with config: %s", CONFIG)

    # Initialize backend
    get_backend(CONFIG.backend, auth_level="write").initialize()

    # Deactivate OAuth2 if requested
    if not CONFIG.external_oauth:
        from entities_service.service.security import verify_token

        LOGGER.warning(
            "Effectively deactivating OAuth2 authentication and authorization. This should NEVER be used "
            "in production."
        )

        async def verify_test_token(
            credentials: Annotated[HTTPAuthorizationCredentials, Depends(SECURITY_SCHEME)]
        ) -> None:
            """Verify a test token."""
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Please log in.",
                headers={"WWW-Authenticate": "Bearer"},
            )

            if not credentials.credentials:
                raise credentials_exception

            if credentials.scheme != "Bearer":
                raise credentials_exception

            if credentials.credentials != CONFIG.test_token.get_secret_value():
                credentials_exception.status_code = status.HTTP_403_FORBIDDEN
                raise credentials_exception

        app.dependency_overrides[verify_token] = verify_test_token

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
