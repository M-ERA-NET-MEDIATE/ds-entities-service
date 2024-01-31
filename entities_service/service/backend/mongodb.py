"""Backend implementation."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field, SecretStr, model_validator
from pymongo.errors import (
    BulkWriteError,
    InvalidDocument,
    OperationFailure,
    PyMongoError,
    WriteConcernError,
    WriteError,
)

from entities_service.models import URI_REGEX, SOFTModelTypes, soft_entity
from entities_service.service.backend import Backends
from entities_service.service.backend.backend import (
    Backend,
    BackendError,
    BackendSettings,
    BackendWriteAccessError,
)
from entities_service.service.config import CONFIG, MongoDsn

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterator, Sequence
    from typing import Any, TypedDict

    from pydantic import AnyHttpUrl
    from pymongo import MongoClient
    from pymongo.collection import Collection as MongoCollection

    from entities_service.models import VersionedSOFTEntity

    class URIParts(TypedDict):
        """The parts of a SOFT entity URI."""

        namespace: str
        version: str
        name: str


LOGGER = logging.getLogger(__name__)


MONGO_CLIENTS: dict[Literal["read", "write"], MongoClient] | None = None
"""Global cache for MongoDB clients.

The key is the available auth levels, i.e. 'read' and 'write'.
"""


BACKEND_DRIVER_MAPPING: dict[Backends, Literal["pymongo", "mongomock"]] = {
    Backends.MONGODB: "pymongo",
    Backends.MONGOMOCK: "mongomock",
}


# Exceptions
class MongoDBBackendError(BackendError, PyMongoError, InvalidDocument):
    """Any MongoDB backend error exception."""


MongoDBBackendWriteAccessError = (
    MongoDBBackendError,
    BackendWriteAccessError,
    WriteConcernError,
    BulkWriteError,
    WriteError,
    OperationFailure,
)
"""Exception raised when write access is denied."""


class MongoDBSettings(BackendSettings):
    """Settings for the MongoDB backend.

    Use default username and password for read access.
    """

    mongo_uri: Annotated[
        MongoDsn, Field(description="The MongoDB URI.")
    ] = CONFIG.mongo_uri

    mongo_username: Annotated[
        str | None, Field(description="The MongoDB username.")
    ] = None

    mongo_password: Annotated[
        SecretStr | None, Field(description="The MongoDB password.")
    ] = None

    mongo_x509_certificate_file: Annotated[
        Path | None,
        Field(
            description=(
                "File path to a X.509 certificate for connecting to the MongoDB "
                "backend with write-access rights."
            ),
        ),
    ] = None

    mongo_ca_file: Annotated[
        Path | None,
        Field(
            description=(
                "File path to a CA certificate for connecting to the MongoDB backend "
                "with write-access rights."
            ),
        ),
    ] = None

    mongo_db: Annotated[
        str, Field(description="The MongoDB database.")
    ] = CONFIG.mongo_db

    mongo_collection: Annotated[
        str, Field(description="The MongoDB collection.")
    ] = CONFIG.mongo_collection

    mongo_driver: Annotated[
        Literal["pymongo", "mongomock"],
        Field(
            description="The MongoDB driver to use. Either 'pymongo' or 'mongomock'.",
        ),
    ] = BACKEND_DRIVER_MAPPING.get(CONFIG.backend, "pymongo")

    auth_level: Annotated[
        Literal["read", "write"],
        Field(description="The auth level to use. Either 'read' or 'write'."),
    ] = "read"

    @model_validator(mode="after")
    def _validate_auth_level_settings(self) -> MongoDBSettings:
        """Ensure the correct settings are set according to the auth level."""
        if self.auth_level == "read":
            if self.mongo_username is None:
                raise ValueError("MongoDB username should be set for read access.")
            if self.mongo_password is None:
                raise ValueError("MongoDB password should be set for read access.")
        else:  # write
            if self.mongo_x509_certificate_file is None:
                raise ValueError(
                    "MongoDB X.509 certificate for connecting with write-access "
                    "rights."
                )
        return self


def get_client(
    auth_level: Literal["read", "write"] = "read",
    uri: str | None = None,
    username: str | None = None,
    password: str | None = None,
    certificate_file: Path | None = None,
    ca_file: Path | None = None,
    driver: Literal["pymongo", "mongomock"] | None = None,
) -> MongoClient:
    """Get the MongoDB client."""
    if driver is None:
        driver = "pymongo"

    if driver == "pymongo":
        from pymongo import MongoClient
    elif driver == "mongomock":
        from mongomock import MongoClient
    else:
        raise ValueError(
            f"Invalid MongoDB driver: {driver}. "
            "Should be either 'pymongo' or 'mongomock'."
        )

    global MONGO_CLIENTS  # noqa: PLW0603

    if auth_level not in ("read", "write"):
        raise ValueError(f"Invalid auth level: {auth_level!r} (valid: 'read', 'write')")

    # Get cached client
    if MONGO_CLIENTS is not None and auth_level in MONGO_CLIENTS:
        LOGGER.debug("Using cached MongoDB client for %r.", auth_level)
        return MONGO_CLIENTS[auth_level]

    LOGGER.debug("Creating new MongoDB client for %r.", username)

    # Ensure all required settings are set
    if auth_level == "read":
        client_options: dict[str, Any] = {
            "username": username or CONFIG.mongo_user,
            "password": password or CONFIG.mongo_password.get_secret_value(),
        }
    else:  # write
        client_options = {
            "tls": True,
            "tlsCertificateKeyFile": str(
                certificate_file or CONFIG.x509_certificate_file
            ),
            "authSource": "$external",
            "authMechanism": "MONGODB-X509",
        }
        if ca_file or CONFIG.ca_file:
            client_options["tlsCAFile"] = str(ca_file or CONFIG.ca_file)

        if client_options["tlsCertificateKeyFile"] is None:
            raise MongoDBBackendError(
                "MongoDB X.509 certificate for connecting with write-access rights "
                "not set."
            )

    new_client = MongoClient(uri or str(CONFIG.mongo_uri), **client_options)

    if MONGO_CLIENTS is None:
        MONGO_CLIENTS = {auth_level: new_client}
    else:
        MONGO_CLIENTS[auth_level] = new_client

    # If using the mongomock backend, there should only ever be one client instance
    # So we set all clients for all auth levels in the cache to the new client
    if driver == "mongomock":
        MONGO_CLIENTS = {
            "read": new_client,
            "write": new_client,
        }

    return MONGO_CLIENTS[auth_level]


class MongoDBBackend(Backend):
    """Backend implementation for MongoDB."""

    _settings_model: type[MongoDBSettings] = MongoDBSettings
    _settings: MongoDBSettings

    def __init__(
        self,
        settings: MongoDBSettings | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(settings)

        try:
            self._collection: MongoCollection = get_client(
                auth_level=self._settings.auth_level,
                uri=str(self._settings.mongo_uri),
                username=self._settings.mongo_username,
                password=(
                    self._settings.mongo_password.get_secret_value()
                    if self._settings.mongo_password
                    else None
                ),
                certificate_file=self._settings.mongo_x509_certificate_file,
                ca_file=self._settings.mongo_ca_file,
                driver=self._settings.mongo_driver,
            )[self._settings.mongo_db][self._settings.mongo_collection]
        except ValueError as exc:
            raise MongoDBBackendError(str(exc)) from exc

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: uri={self._settings.mongo_uri}"

    # Exceptions
    @property
    def write_access_exception(self) -> tuple:
        return MongoDBBackendWriteAccessError

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._collection.find({}, projection={"_id": False}))

    def __len__(self) -> int:
        return self._collection.count_documents({})

    def initialize(self) -> None:
        """Initialize the MongoDB backend."""
        # Check index exists
        if "URI" in (indices := self._collection.index_information()):
            if not indices["URI"].get("unique", False):
                LOGGER.warning(
                    "The URI index in the MongoDB collection is not unique. "
                    "This may cause problems when creating entities."
                )
            if indices["URI"].get("key", False) != [
                ("uri", 1),
                ("namespace", 1),
                ("version", 1),
                ("name", 1),
            ]:
                LOGGER.warning(
                    "The URI index in the MongoDB collection is not as expected. "
                    "This may cause problems when creating entities."
                )
            return

        # Create a unique index for the URI
        self._collection.create_index(
            ["uri", "namespace", "version", "name"], unique=True, name="URI"
        )

    def create(
        self, entities: Sequence[VersionedSOFTEntity | dict[str, Any]]
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Create one or more entities in the MongoDB."""
        LOGGER.info("Creating entities: %s", entities)
        LOGGER.info("The creator's user name: %s", self._settings.mongo_username)

        entities = [self._prepare_entity(entity) for entity in entities]

        result = self._collection.insert_many(entities)
        if len(result.inserted_ids) > 1:
            return list(
                self._collection.find(
                    {"_id": {"$in": result.inserted_ids}}, projection={"_id": False}
                )
            )

        return self._collection.find_one(
            {"_id": result.inserted_ids[0]}, projection={"_id": False}
        )

    def read(self, entity_identity: AnyHttpUrl | str) -> dict[str, Any] | None:
        """Read an entity from the MongoDB."""
        filter = self._single_uri_query(str(entity_identity))
        return self._collection.find_one(filter, projection={"_id": False})

    def update(
        self,
        entity_identity: AnyHttpUrl | str,
        entity: VersionedSOFTEntity | dict[str, Any],
    ) -> None:
        """Update an entity in the MongoDB."""
        entity = self._prepare_entity(entity)
        filter = self._single_uri_query(str(entity_identity))
        self._collection.update_one(filter, {"$set": entity})

    def delete(self, entity_identity: AnyHttpUrl | str) -> None:
        """Delete an entity in the MongoDB."""
        filter = self._single_uri_query(str(entity_identity))
        self._collection.delete_one(filter)

    def search(self, query: Any) -> Iterator[dict[str, Any]]:
        """Search for entities."""
        query = query or {}

        if not isinstance(query, dict):
            raise TypeError(f"Query must be a dict for {self.__class__.__name__}.")

        return self._collection.find(query, projection={"_id": False})

    def count(self, query: Any = None) -> int:
        """Count entities."""
        query = query or {}

        if not isinstance(query, dict):
            raise TypeError(f"Query must be a dict for {self.__class__.__name__}.")

        return self._collection.count_documents(query)

    def close(self) -> None:
        """We never close the MongoDB connection once its created."""
        if self._settings.mongo_driver == "mongomock":
            return

        super().close()

    # MongoDBBackend specific methods
    def _single_uri_query(self, uri: str) -> dict[str, Any]:
        """Build a query for a single URI."""
        if (match := URI_REGEX.match(uri)) is not None:
            uri_parts: URIParts = match.groupdict()  # type: ignore[assignment]
        else:
            raise ValueError(f"Invalid entity URI: {uri}")

        if not all(uri_parts.values()):
            raise ValueError(f"Invalid entity URI: {uri}")

        return {"$or": [uri_parts, {"uri": uri}]}

    def _prepare_entity(
        self, entity: VersionedSOFTEntity | dict[str, Any]
    ) -> dict[str, Any]:
        """Clean and prepare the entity for interactions with the MongoDB backend."""
        if isinstance(entity, dict):
            uri = entity.get("uri", None) or (
                f"{entity.get('namespace', '')}/{entity.get('version', '')}"
                f"/{entity.get('name', '')}"
            )
            entity = soft_entity(
                error_msg=f"Invalid entity given for {uri}.",
                **entity,
            )

        if not isinstance(entity, SOFTModelTypes):
            raise TypeError(
                "Entity must be a dict or a SOFTModelTypes for "
                f"{self.__class__.__name__}."
            )

        entity = entity.model_dump(by_alias=True, mode="json", exclude_unset=True)

        # Convert all '$ref' to 'ref' in the entity
        if isinstance(entity["properties"], list):  # SOFT5
            for index, property_value in enumerate(list(entity["properties"])):
                entity["properties"][index] = {
                    key.replace("$", ""): value for key, value in property_value.items()
                }

        elif isinstance(entity["properties"], dict):  # SOFT7
            for property_name, property_value in list(entity["properties"].items()):
                entity["properties"][property_name] = {
                    key.replace("$", ""): value for key, value in property_value.items()
                }

        else:
            raise TypeError(
                f"Invalid entity properties type: {type(entity['properties'])}"
            )

        return entity
