"""The main application module."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from dataspaces_entities import __version__
from dataspaces_entities.backend import get_backend
from dataspaces_entities.config import get_config
from dataspaces_entities.exception_handlers import DS_ENTITIES_EXCEPTIONS
from dataspaces_entities.exceptions import DSEntitiesGeneralException, InvalidEntityError
from dataspaces_entities.models import ErrorResponse
from dataspaces_entities.routers import get_routers

logger = logging.getLogger(__name__)

# Handle testing
if os.getenv("DS_ENTITIES_DISABLE_AUTH_ROLE_CHECKS", "false").lower() in ("1", "true", "yes", "on"):
    import dataspaces_auth.fastapi._auth as ds_auth
    from dataspaces_auth.fastapi._models import TokenData

    from dataspaces_entities.models import DSAPIRole

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
    config = get_config()

    logger.debug("DataSpaces-Entities configuration: %s", config)

    # Initialize backend
    get_backend(config.backend).initialize()

    if os.getenv("DS_ENTITIES_DISABLE_AUTH_ROLE_CHECKS", "false").lower() in ("1", "true", "yes", "on"):
        logger.debug(
            "Running in test mode.\n"
            "    - External OAuth2 authentication is disabled!\n"
            "    - DataSpaces-Auth role checks are disabled!"
        )

    # Run application
    yield


def create_app() -> FastAPI:
    """Create the ASGI application for the DataSpaces-Entities service."""
    app = FastAPI(
        title="Entities Service for DataSpaces",
        version=__version__,
        description="A service for managing entities in DataSpaces.",
        lifespan=lifespan,
        debug=get_config().debug,
        responses={
            InvalidEntityError.status_code: {
                "description": "The provided request parameters (e.g., Entity/-ies) are invalid.",
                "model": ErrorResponse,
            },
            DSEntitiesGeneralException.status_code: {
                "description": "A general server error occurred.",
                "model": ErrorResponse,
            },
        },
    )

    # Add routers
    for router in get_routers():
        app.include_router(router)

    # Add exception handlers
    for exception, handler in DS_ENTITIES_EXCEPTIONS:
        app.add_exception_handler(exception, handler)

    return app
