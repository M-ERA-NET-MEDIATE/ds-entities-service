"""The main application module."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from entities_service import __version__
from entities_service.backend import get_backend
from entities_service.config import get_config
from entities_service.logger import setup_logger
from entities_service.routers import get_routers

LOGGER = logging.getLogger(__name__)

# Handle testing
if bool(int(os.getenv("DS_ENTITIES_SERVICE_DISABLE_AUTH_ROLE_CHECKS", "0"))):
    import dataspaces_auth.fastapi._auth as ds_auth
    from dataspaces_auth.fastapi._models import TokenData

    from entities_service.models import DSAPIRole

    # Override DataSpaces-Auth valid_access_token dependency
    async def disable_auth_valid_access_token() -> TokenData:
        return TokenData(
            # Role mapping
            resource_access={
                "backend": {
                    "roles": [
                        DSAPIRole.ENTITIES_ADMIN,
                        DSAPIRole.ENTITIES_DELETE,
                        DSAPIRole.ENTITIES_READ,
                        DSAPIRole.ENTITIES_WRITE,
                        DSAPIRole.ENTITIES_EDIT,
                    ]
                },
                # Required resource_access field (for the model)
                "account": {"roles": []},
            },
            # Required fields (for the model)
            preferred_username="test_user",
            iss="https://semanticmatter.com",
            exp=1234567890,
            aud=["test_client"],
            sub="test_user",
            iat=1234567890,
            jti="test_jti",
        )

    ds_auth.valid_access_token = disable_auth_valid_access_token


# Application lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Add lifespan events to the application."""
    # Initialize logger
    setup_logger()

    config = get_config()

    LOGGER.debug("Starting service with config: %s", config)

    # Initialize backend
    get_backend(config.backend, auth_level="write").initialize()

    if bool(int(os.getenv("DS_ENTITIES_SERVICE_DISABLE_AUTH_ROLE_CHECKS", "0"))):
        LOGGER.debug(
            "Running in test mode.\n"
            "    - External OAuth2 authentication is disabled!\n"
            "    - DataSpaces-Auth role checks are disabled!"
        )

    # Run application
    yield


def create_app() -> FastAPI:
    """Create the ASGI application for the DataSpaces-Entities service."""
    config = get_config()

    app = FastAPI(
        title="Entities Service for DataSpaces",
        version=__version__,
        description="A service for managing entities in DataSpaces.",
        lifespan=lifespan,
        debug=config.debug,
    )

    # Add routers
    for router in get_routers():
        app.include_router(router)

    return app
