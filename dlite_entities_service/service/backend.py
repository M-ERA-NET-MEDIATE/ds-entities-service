"""Backend implementation."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pymongo import MongoClient

from dlite_entities_service.service.config import CONFIG

if TYPE_CHECKING:  # pragma: no cover
    from pymongo.collection import Collection


def get_collection(
    uri: str | None = None, username: str | None = None, password: str | None = None
) -> Collection:
    """Get the MongoDB collection for entities."""
    client_kwargs = {
        "username": username or CONFIG.mongo_user,
        "password": password
        or (
            CONFIG.mongo_password.get_secret_value()
            if CONFIG.mongo_password is not None
            else None
        ),
    }
    for key, value in list(client_kwargs.items()):
        if value is None:
            client_kwargs.pop(key, None)

    mongo_client = MongoClient(
        uri or str(CONFIG.mongo_uri),
        **client_kwargs,
    )
    return mongo_client.dlite.entities


ENTITIES_COLLECTION = get_collection()
