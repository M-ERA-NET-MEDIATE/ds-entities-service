"""Backend implementation."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Literal, get_args

from bson import ObjectId
from pydantic import Field, SecretStr, ValidationError
from pymongo.errors import (
    BulkWriteError,
    DuplicateKeyError,
    InvalidDocument,
    OperationFailure,
    PyMongoError,
    WriteConcernError,
    WriteError,
)
from s7 import SOFT7Entity, get_entity
from s7.pydantic_models.soft7_entity import SOFT7IdentityURI, SOFT7IdentityURIType

from dataspaces_entities.backend import Backends
from dataspaces_entities.backend.backend import (
    Backend,
    BackendError,
    BackendSettings,
    BackendWriteAccessError,
)
from dataspaces_entities.config import MongoDsn, get_config
from dataspaces_entities.exceptions import EntityExists, InvalidEntityError
from dataspaces_entities.utils import generate_error_display_ids, get_identity

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator, Iterable, Iterator
    from typing import Any

    from pymongo import MongoClient
    from pymongo.collection import Collection as MongoCollection
    from s7 import SOFT7Entity


logger = logging.getLogger(__name__)


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

    mongo_uri: Annotated[MongoDsn, Field(description="The MongoDB URI.")] = get_config().mongo_uri

    mongo_username: Annotated[str | None, Field(description="The MongoDB username.")] = None

    mongo_password: Annotated[SecretStr | None, Field(description="The MongoDB password.")] = None

    mongo_db: Annotated[str, Field(description="The MongoDB database.")] = get_config().mongo_db

    mongo_collection: Annotated[str, Field(description="The MongoDB collection.")] = (
        get_config().mongo_collection
    )

    mongo_driver: Annotated[
        Literal["pymongo"],
        Field(
            description="The MongoDB driver to use. Only 'pymongo' is currently supported.",
        ),
    ] = BACKEND_DRIVER_MAPPING.get(get_config().backend, "pymongo")


@lru_cache
def get_client(
    uri: str | None = None,
    driver: Literal["pymongo"] | None = None,
) -> MongoClient:
    """Get the MongoDB client."""
    config = get_config()

    if driver is None:
        driver = "pymongo"

    if driver == "pymongo":
        from pymongo import MongoClient
    else:
        raise ValueError(f"Invalid MongoDB driver: {driver}. Only 'pymongo' is currently supported.")

    logger.debug("Creating new MongoDB client.")

    return MongoClient(
        uri or str(config.mongo_uri),
        username=config.mongo_user,
        password=config.mongo_password.get_secret_value(),
    )


class MongoDBBackend(Backend):
    """Backend implementation for MongoDB.

    Represents a single collection in a MongoDB database.
    """

    _settings_model: type[MongoDBSettings] = MongoDBSettings
    _settings: MongoDBSettings

    def __init__(
        self,
        settings: MongoDBSettings | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(settings)

        try:
            self._collection: MongoCollection = get_client(
                uri=str(self._settings.mongo_uri),
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
                logger.warning(
                    "The IDENTITY index in the MongoDB collection is not unique. "
                    "This may cause problems when creating entities."
                )
            if indices["IDENTITY"].get("key", False) != [("identity", 1)]:
                logger.warning(
                    "The IDENTITY index in the MongoDB collection is not as expected. "
                    "This may cause problems when creating entities."
                )
            return

        # Create a unique index for the IDENTITY
        self._collection.create_index(["identity"], unique=True, name="IDENTITY")

    def create(
        self, entities: Iterable[SOFT7Entity | dict[str, Any]]
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Create one or more entities in the MongoDB.

        Parameters:
            entities: The entities to create.

        Returns:
            The created entities.

        Raises:
            EntityExists: If one or more entities already exist.

        """
        logger.info("Creating entities: %s", entities)
        logger.info("The creator's user name: %s", self._settings.mongo_username)

        entities = [self._prepare_entity(entity) for entity in entities]

        try:
            result = self._collection.insert_many(entities)
        except (DuplicateKeyError, BulkWriteError) as exc:
            # Check if BulkWriteError is due to duplicate key error
            if isinstance(exc, BulkWriteError):
                if not any(error.get("code") == 11000 for error in exc.details.get("writeErrors", [])):
                    raise

                logger.error("Bulk write error due to duplicate key error: %s", exc)

            # One or more entities already exist
            entity_ids = [get_identity(entity) for entity in entities]
            existing_entities = list(self.search(by_identities=entity_ids))
            existing_entity_ids = [get_identity(entity) for entity in existing_entities]

            logger.exception(
                "Could not create entities, one or more already exist: %s",
                ", ".join(existing_entity_ids),
            )

            display_ids_str = ", ".join(generate_error_display_ids(entity_ids=existing_entity_ids))

            raise EntityExists(
                entity_id=display_ids_str,
                detail=(
                    "Cannot create entit"
                    "{suffix} with identit{suffix} already existing: {identities}".format(
                        suffix="y" if len(existing_entity_ids) == 1 else "ies",
                        identities=display_ids_str,
                    )
                ),
            ) from exc

        if len(result.inserted_ids) > 1:
            return list(self.search(by_mongo_ids=result.inserted_ids))

        return self._collection.find_one({"_id": result.inserted_ids[0]}, projection={"_id": False})

    def read(self, entity_identity: SOFT7IdentityURIType | str) -> dict[str, Any] | None:
        """Read an entity from the MongoDB.

        Parameters:
            entity_identity: The identity of the entity to read.

        Returns:
            The entity data, or None if not found.

        """
        query_filter = self._single_identity_query(entity_identity)
        return self._collection.find_one(query_filter, projection={"_id": False})

    def update(
        self,
        entity_identity: SOFT7IdentityURIType | str,
        entity: SOFT7Entity | dict[str, Any],
    ) -> None:
        """Update an entity in the MongoDB.

        Parameters:
            entity_identity: The identity of the entity to update.
            entity: The entity data to update.

        Raises:
            MongoDBBackendError: If the update fails.

        """
        entity = self._prepare_entity(entity)
        query_filter = self._single_identity_query(entity_identity)
        self._collection.update_one(query_filter, {"$set": entity})

    def delete(self, entity_identities: Iterable[SOFT7IdentityURIType | str]) -> None:
        """Delete one or more entities in the MongoDB.

        Parameters:
            entity_identities: The identities of the entities to delete.

        Raises:
            InvalidEntityError: If one or more identities are invalid.

        """
        for identity in entity_identities:
            if isinstance(identity, str):
                try:
                    SOFT7IdentityURI(identity)
                except (TypeError, ValidationError) as exc:
                    raise InvalidEntityError(f"Invalid entity identity: {identity}") from exc

        query_filter = {"identity": {"$in": [str(identity) for identity in entity_identities]}}

        self._collection.delete_many(
            query_filter,
            comment="deleting via the DS Entities Service MongoDB backend delete() method",
        )

    def search(
        self,
        raw_query: Any = None,
        by_properties: list[str] | None = None,
        by_dimensions: list[str] | None = None,
        by_identities: list[SOFT7IdentityURIType] | list[str] | None = None,
        by_mongo_ids: list[ObjectId] | list[str] | None = None,
    ) -> Generator[dict[str, Any]]:
        """Search for entities.

        If `raw_query` is given, it will be used as the query. Otherwise, the `by_properties`,
        `by_dimensions`, `by_identities`, and `by_mongo_ids` will be used to construct the query.
        Note, all parameters are combined using a logical OR.

        Parameters:
            raw_query: The raw MongoDB query to use.
            by_properties: List of property names to search for.
            by_dimensions: List of dimension names to search for.
            by_identities: List of entity identities to search for.
            by_mongo_ids: List of MongoDB document IDs to search for.

        Yields:
            Matching entities.

        Raises:
            MongoDBBackendError: If the query is invalid.
            InvalidEntityError: If one or more entity identities are invalid.

        """
        query = raw_query or {}

        if not isinstance(query, dict):
            raise MongoDBBackendError(f"Query must be a dict for {self.__class__.__name__}.")

        if not query:
            if any((by_properties, by_dimensions, by_identities, by_mongo_ids)):
                query = {"$or": []}

            if by_properties:
                if not isinstance(by_properties, list) or not all(
                    isinstance(prop, str) for prop in by_properties
                ):
                    raise MongoDBBackendError("by_properties must be a list of strings.")

                query["$or"].extend(
                    [
                        {"properties": {"$in": by_properties}},
                        {"properties.name": {"$in": by_properties}},
                    ]
                )
            if by_dimensions:
                if not isinstance(by_dimensions, list) or not all(
                    isinstance(dim, str) for dim in by_dimensions
                ):
                    raise MongoDBBackendError("by_dimensions must be a list of strings.")

                query["$or"].extend(
                    [
                        {"dimension": {"$in": by_dimensions}},
                        {"dimension.name": {"$in": by_dimensions}},
                    ]
                )
            if by_identities:
                if not isinstance(by_identities, list) or not all(
                    isinstance(identity, (str, *get_args(SOFT7IdentityURIType)))
                    for identity in by_identities
                ):
                    raise MongoDBBackendError(
                        "by_identities must be a list of strings or SOFT7IdentityURI."
                    )

                for identity in by_identities:
                    if isinstance(identity, str):
                        try:
                            SOFT7IdentityURI(identity)
                        except (TypeError, ValidationError) as exc:
                            raise InvalidEntityError(f"Invalid entity identity: {identity}") from exc

                query["$or"].extend(
                    [
                        {"identity": {"$in": [str(identity) for identity in by_identities]}},
                    ]
                )
            if by_mongo_ids:
                if not isinstance(by_mongo_ids, list) or not all(
                    isinstance(mongo_id, (str, ObjectId)) for mongo_id in by_mongo_ids
                ):
                    raise MongoDBBackendError(
                        "by_mongo_ids must be a list of strings or ObjectId instances."
                    )

                query["$or"].extend(
                    [
                        {
                            "_id": {
                                "$in": [
                                    mongo_id if isinstance(mongo_id, ObjectId) else ObjectId(mongo_id)
                                    for mongo_id in by_mongo_ids
                                ]
                            }
                        },
                    ]
                )

        cursor = self._collection.find(
            query,
            projection={"_id": False},
            comment="search via the DS Entities Service MongoDB backend search() method",
        )
        yield from cursor

    def count(self, raw_query: Any = None) -> int:
        """Count entities.

        Parameters:
            raw_query: The raw MongoDB query to use.

        Returns:
            The number of matching entities.

        Raises:
            MongoDBBackendError: If the query is invalid.

        """
        query = raw_query or {}

        if not isinstance(query, dict):
            raise MongoDBBackendError(f"Query must be a dict for {self.__class__.__name__}.")

        return self._collection.count_documents(query)

    # MongoDBBackend specific methods
    def _single_identity_query(self, identity: SOFT7IdentityURIType | str) -> dict[str, Any]:
        """Build a query for a single identity.

        Parameters:
            identity: The identity to build the query for.

        Returns:
            The query as a dictionary.

        Raises:
            InvalidEntityError: If the identity is invalid.

        """
        if isinstance(identity, str):
            try:
                SOFT7IdentityURI(identity)
            except (TypeError, ValidationError) as exc:
                raise InvalidEntityError(f"Invalid entity identity: {identity}") from exc

        return {"identity": str(identity)}

    def _prepare_entity(self, entity: SOFT7Entity | dict[str, Any]) -> dict[str, Any]:
        """Prepare the entity for interactions with the MongoDB backend.

        Parameters:
            entity: The entity to prepare.

        Returns:
            The prepared entity as a dictionary.

        Raises:
            TypeError: If the entity is not a dict or SOFT7Entity.

        """
        if isinstance(entity, dict):
            entity = get_entity(entity)

        if not isinstance(entity, SOFT7Entity):
            raise TypeError(
                "Entity must be a dict or a SOFT7Entity for "
                f"{self.__class__.__name__}, got a {type(entity)}."
            )

        return entity.model_dump(mode="json", exclude_unset=True)
