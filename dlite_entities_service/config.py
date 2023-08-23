"""Service app configuration."""
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic.networks import AnyHttpUrl, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    """Service app configuration."""

    base_url: AnyHttpUrl = Field(
        AnyHttpUrl("http://onto-ns.com/meta"),
        description="Base URL, where the service is running.",
    )
    mongo_uri: MongoDsn = Field(
        MongoDsn("mongodb://localhost:27017"),
        description="URI for the MongoDB cluster/server.",
    )
    mongo_user: str | None = Field(
        None, description="Username for connecting to the MongoDB."
    )
    mongo_password: SecretStr | None = Field(
        None, description="Password for connecting to the MongoDB."
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def _strip_ending_slashes(cls, value: Any) -> AnyHttpUrl:
        """Strip any end forward slashes."""
        return AnyHttpUrl(str(value).rstrip("/"))

    model_config = SettingsConfigDict(env_prefix="entity_service_", env_file=".env")


CONFIG = ServiceSettings()
