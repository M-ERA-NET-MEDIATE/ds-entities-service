"""The main application module."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from entities_service import __version__
from entities_service.service.backend import get_backend
from entities_service.service.config import CONFIG
from entities_service.service.logger import setup_logger
from entities_service.service.routers import get_routers

LOGGER = logging.getLogger("entities_service")


# Handle testing
env_vars: set[str] = set()
if bool(int(os.getenv("DS_ENTITIES_SERVICE_DISABLE_AUTH_ROLE_CHECKS", "0"))):
    from entities_service.models import DSAPIRole

    # Set mandatory settings for DataSpaces-Auth
    env_vars = {"authorization_url", "token_url", "certs_url", "scopes"}
    env_vars_to_unset: set[str] = set()
    original_env_var_values: dict[str, str] = {}

    for env_var in env_vars:
        composed_env_var = f"DS_AUTH_{env_var.upper()}"
        if composed_env_var in os.environ:
            original_env_var_values[composed_env_var] = os.environ[composed_env_var]
        else:
            env_vars_to_unset.add(composed_env_var)

        if "url" in env_var:
            os.environ[composed_env_var] = "https://semanticmatter.com"
        else:
            os.environ[composed_env_var] = '["openid","profile","email"]'

    # Override DataSpaces-Auth valid_access_token dependency
    import dataspaces_auth.fastapi._auth as ds_auth
    from dataspaces_auth.fastapi._models import TokenData

    ds_auth.valid_access_token = lambda: TokenData(
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


# Application lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Add lifespan events to the application."""
    # Initialize logger
    setup_logger()

    LOGGER.debug("Starting service with config: %s", CONFIG)

    # Initialize backend
    get_backend(CONFIG.backend, auth_level="write").initialize()

    if bool(int(os.getenv("DS_ENTITIES_SERVICE_DISABLE_AUTH_ROLE_CHECKS", "0"))):
        LOGGER.debug(
            "Running in test mode.\n"
            "    - External OAuth2 authentication is disabled!\n"
            "    - DataSpaces-Auth role checks are disabled!"
        )

    # Run application
    yield

    ## Clean up

    # Close MongoDB clients (if any)
    from entities_service.service.backend.mongodb import MONGO_CLIENTS

    if MONGO_CLIENTS is not None:
        for role in list(MONGO_CLIENTS):
            MONGO_CLIENTS.pop(role).close()

    # Handle environment variables if in test mode
    if env_vars:
        # Unset previously undefined env vars
        for env_var in env_vars_to_unset:
            os.environ.pop(env_var)

        # Reset original values for pre-defined env vars
        for env_var, value in original_env_var_values.items():
            os.environ[env_var] = value


# Setup application
APP = FastAPI(
    title="Entities Service for DataSpaces",
    version=__version__,
    description="A service for managing entities in DataSpaces.",
    lifespan=lifespan,
    debug=CONFIG.debug,
)

# Add routers
for router in get_routers():
    APP.include_router(router)
