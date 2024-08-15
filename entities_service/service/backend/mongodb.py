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
from s7 import SOFT7Entity, get_entity

from entities_service.models import URI_REGEX
from entities_service.service.backend import Backends
from entities_service.service.backend.backend import (
    Backend,
    BackendError,
    BackendSettings,
    BackendWriteAccessError,
)
from entities_service.service.config import CONFIG, MongoDsn

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator, Iterable, Iterator
    from typing import Any

    from pydantic import AnyHttpUrl
    from pymongo import MongoClient
    from pymongo.collection import Collection as MongoCollection
    from s7 import SOFT7Entity


LOGGER = logging.getLogger(__name__)


MONGO_CLIENTS: dict[Literal["read", "write"], MongoClient] | None = None
"""Global cache for MongoDB clients.

The key is the available auth levels, i.e. 'read' and 'write'.
"""


BACKEND_DRIVER_MAPPING: dict[Backends, Literal["pymongo"]] = {
    Backends.MONGODB: "pymongo",
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

    mongo_uri: Annotated[MongoDsn, Field(description="The MongoDB URI.")] = CONFIG.mongo_uri

    mongo_username: Annotated[str | None, Field(description="The MongoDB username.")] = None

    mongo_password: Annotated[SecretStr | None, Field(description="The MongoDB password.")] = None

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

    mongo_db: Annotated[str, Field(description="The MongoDB database.")] = CONFIG.mongo_db

    mongo_collection: Annotated[str, Field(description="The MongoDB collection.")] = CONFIG.mongo_collection

    mongo_driver: Annotated[
        Literal["pymongo"],
        Field(
            description="The MongoDB driver to use. Only 'pymongo' is currently supported.",
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
                raise ValueError("MongoDB X.509 certificate for connecting with write-access rights.")
        return self


def get_client(
    auth_level: Literal["read", "write"] = "read",
    uri: str | None = None,
    username: str | None = None,
    password: str | None = None,
    certificate_file: Path | None = None,
    ca_file: Path | None = None,
    driver: Literal["pymongo"] | None = None,
) -> MongoClient:
    """Get the MongoDB client."""
    if driver is None:
        driver = "pymongo"

    if driver == "pymongo":
        from pymongo import MongoClient
    else:
        raise ValueError(f"Invalid MongoDB driver: {driver}. Only 'pymongo' is currently supported.")

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
            "tlsCertificateKeyFile": str(certificate_file or CONFIG.x509_certificate_file),
            "authSource": "$external",
            "authMechanism": "MONGODB-X509",
        }
        if ca_file or CONFIG.ca_file:
            client_options["tlsCAFile"] = str(ca_file or CONFIG.ca_file)

        if client_options["tlsCertificateKeyFile"] is None:
            raise MongoDBBackendError(
                "MongoDB X.509 certificate for connecting with write-access rights not set."
            )

    new_client = MongoClient(uri or str(CONFIG.mongo_uri), **client_options)

    if MONGO_CLIENTS is None:
        MONGO_CLIENTS = {auth_level: new_client}
    else:
        MONGO_CLIENTS[auth_level] = new_client

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
        if "IDENTITY" in (indices := self._collection.index_information()):
            if not indices["IDENTITY"].get("unique", False):
                LOGGER.warning(
                    "The IDENTITY index in the MongoDB collection is not unique. "
                    "This may cause problems when creating entities."
                )
            if indices["IDENTITY"].get("key", False) != [("identity", 1)]:
                LOGGER.warning(
                    "The IDENTITY index in the MongoDB collection is not as expected. "
                    "This may cause problems when creating entities."
                )
            return

        # Create a unique index for the IDENTITY
        self._collection.create_index(["identity"], unique=True, name="IDENTITY")

    def create(
        self, entities: Iterable[SOFT7Entity | dict[str, Any]]
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Create one or more entities in the MongoDB."""
        LOGGER.info("Creating entities: %s", entities)
        LOGGER.info("The creator's user name: %s", self._settings.mongo_username)

        entities = [self._prepare_entity(entity) for entity in entities]

        result = self._collection.insert_many(entities)
        if len(result.inserted_ids) > 1:
            return list(
                self._collection.find({"_id": {"$in": result.inserted_ids}}, projection={"_id": False})
            )

        return self._collection.find_one({"_id": result.inserted_ids[0]}, projection={"_id": False})

    def read(self, entity_identity: AnyHttpUrl | str) -> dict[str, Any] | None:
        """Read an entity from the MongoDB."""
        filter = self._single_identity_query(str(entity_identity))
        return self._collection.find_one(filter, projection={"_id": False})

    def update(
        self,
        entity_identity: AnyHttpUrl | str,
        entity: SOFT7Entity | dict[str, Any],
    ) -> None:
        """Update an entity in the MongoDB."""
        entity = self._prepare_entity(entity)
        filter = self._single_identity_query(str(entity_identity))
        self._collection.update_one(filter, {"$set": entity})

    def delete(self, entity_identities: Iterable[AnyHttpUrl | str]) -> None:
        """Delete one or more entities in the MongoDB."""
        for identity in entity_identities:
            if URI_REGEX.match(str(identity)) is None:
                raise MongoDBBackendError(f"Invalid entity identity: {identity}")

        filter = {"identity": {"$in": [str(identity) for identity in entity_identities]}}

        self._collection.delete_many(
            filter,
            # comment=(
            #     "deleting via the DS Entities Service MongoDB backend delete() method"
            # ),
        )

    def search(
        self,
        raw_query: Any = None,
        by_properties: list[str] | None = None,
        by_dimensions: list[str] | None = None,
        by_identity: list[AnyHttpUrl] | list[str] | None = None,
    ) -> Generator[dict[str, Any]]:
        """Search for entities.

        If `raw_query` is given, it will be used as the query. Otherwise, the
        `by_properties`, `by_dimensions`, and `by_identity` will be used to
        construct the query.
        """
        query = raw_query or {}

        if not isinstance(query, dict):
            raise MongoDBBackendError(f"Query must be a dict for {self.__class__.__name__}.")

        if not query:
            if any((by_properties, by_dimensions, by_identity)):
                query = {"$or": []}

            if by_properties:
                query["$or"].extend(
                    [
                        {"properties": {"$in": by_properties}},
                        {"properties.name": {"$in": by_properties}},
                    ]
                )
            if by_dimensions:
                query["$or"].extend(
                    [
                        {"dimension": {"$in": by_dimensions}},
                        {"dimension.name": {"$in": by_dimensions}},
                    ]
                )
            if by_identity:
                for identity in by_identity:
                    if URI_REGEX.match(str(identity)) is None:
                        raise ValueError(f"Invalid entity identity: {identity}")

                query["$or"].extend(
                    [
                        {"identity": {"$in": [str(identity) for identity in by_identity]}},
                    ]
                )

        cursor = self._collection.find(
            query,
            projection={"_id": False},
            # comment=(
            #     "search via the DS Entities Service MongoDB backend search() method"
            # ),
        )
        yield from cursor

    def count(self, raw_query: Any = None) -> int:
        """Count entities."""
        query = raw_query or {}

        if not isinstance(query, dict):
            raise MongoDBBackendError(f"Query must be a dict for {self.__class__.__name__}.")

        return self._collection.count_documents(query)

    # MongoDBBackend specific methods
    def _single_identity_query(self, identity: str) -> dict[str, Any]:
        """Build a query for a single identity."""
        if URI_REGEX.match(identity) is None:
            raise ValueError(f"Invalid entity identity: {identity}")

        return {"identity": identity}

    def _prepare_entity(self, entity: SOFT7Entity | dict[str, Any]) -> dict[str, Any]:
        """Prepare the entity for interactions with the MongoDB backend."""
        if isinstance(entity, dict):
            entity = get_entity(entity)

        if not isinstance(entity, SOFT7Entity):
            raise TypeError(
                "Entity must be a dict or a SOFT7Entity for "
                f"{self.__class__.__name__}, got a {type(entity)}."
            )

        return entity.model_dump(mode="json", exclude_unset=True)
