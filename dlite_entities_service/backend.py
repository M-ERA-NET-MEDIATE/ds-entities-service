"""Backend implementation."""
from __future__ import annotations

from pymongo import MongoClient

from dlite_entities_service.config import CONFIG

client_kwargs = {
    "username": CONFIG.mongo_user,
    "password": CONFIG.mongo_password.get_secret_value()
    if CONFIG.mongo_password is not None
    else None,
}
for key, value in list(client_kwargs.items()):
    if value is None:
        client_kwargs.pop(key, None)


MONGO_CLIENT = MongoClient(
    str(CONFIG.mongo_uri),
    **client_kwargs,
)
MONGO_DB = MONGO_CLIENT.dlite

ENTITIES_COLLECTION = MONGO_DB.entities
