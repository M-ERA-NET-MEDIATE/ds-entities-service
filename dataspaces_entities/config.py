"""Service app configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from dataspaces_utils.fastapi.settings import DataSpacesSettings
from pydantic import Field, SecretStr
from pydantic.networks import UrlConstraints
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict

from dataspaces_entities.backend import Backends

MongoDsn = Annotated[MultiHostUrl, UrlConstraints(allowed_schemes=["mongodb", "mongodb+srv"])]
"""Support MongoDB schemes with hidden port (avoid default_port constraint)."""


class ServiceConfig(DataSpacesSettings):
    """Service app configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DS_ENTITIES_", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    backend: Annotated[
        Backends,
        Field(
            description="Backend to use for storing entities.",
        ),
    ] = Backends.MONGODB

    max_entities_in_errors: Annotated[
        int,
        Field(
            description="Maximum number of entities to include in error messages.",
            ge=1,
        ),
    ] = 5

    # MongoDB backend settings
    mongo_uri: Annotated[
        MongoDsn,
        Field(
            description="URI for the MongoDB cluster/server.",
        ),
    ] = MongoDsn("mongodb://localhost:27017")

    mongo_user: Annotated[
        str,
        Field(description="Username for connecting to the MongoDB with read-only rights."),
    ] = "dataspaces"

    mongo_password: Annotated[
        SecretStr,
        Field(description="Password for connecting to the MongoDB with read-only rights."),
    ] = SecretStr("dataspaces")

    mongo_db: Annotated[
        str,
        Field(
            description="Name of the MongoDB database for storing entities in the Entities Service.",
        ),
    ] = "entities_service"

    mongo_collection: Annotated[
        str,
        Field(
            description="Name of the MongoDB collection for storing entities.",
        ),
    ] = "entities"


# The configuration is an LRU-cached function to avoid re-reading the environment variables.
# This is done for both historical and performance reasons.
# THe historical reason is that this used to simply be a module-level variable, which was
# auto-initialized on any import of this package, which can lead to unwanted side effects due to the way
# the configuration is setup. The performance reason is that the configuration is accessed in many places,
# and we don't want to re-read the environment variables each time.
@lru_cache
def get_config() -> ServiceConfig:
    """Get the service configuration."""
    return ServiceConfig()
