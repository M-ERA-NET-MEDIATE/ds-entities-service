"""Service app configuration."""
from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field, SecretStr, field_validator
from pydantic.networks import AnyHttpUrl, MultiHostUrl, UrlConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

MongoDsn = Annotated[
    MultiHostUrl, UrlConstraints(allowed_schemes=["mongodb", "mongodb+srv"])
]
"""Support MongoDB schemes with hidden port (no default port)."""


class ServiceSettings(BaseSettings):
    """Service app configuration."""

    base_url: Annotated[
        AnyHttpUrl,
        Field(
            description="Base URL, where the service is running.",
        ),
    ] = AnyHttpUrl("http://onto-ns.com/meta")
    mongo_uri: Annotated[
        MongoDsn,
        Field(
            description="URI for the MongoDB cluster/server.",
        ),
    ] = MongoDsn("mongodb://localhost:27017")
    mongo_user: Annotated[
        str | None, Field(description="Username for connecting to the MongoDB.")
    ] = None
    mongo_password: Annotated[
        SecretStr | None, Field(description="Password for connecting to the MongoDB.")
    ] = None

    @field_validator("base_url", mode="before")
    @classmethod
    def _strip_ending_slashes(cls, value: Any) -> AnyHttpUrl:
        """Strip any end forward slashes."""
        return AnyHttpUrl(str(value).rstrip("/"))

    model_config = SettingsConfigDict(env_prefix="entity_service_", env_file=".env")


CONFIG = ServiceSettings()
