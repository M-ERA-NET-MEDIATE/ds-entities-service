"""Backend implementation."""
from pymongo import MongoClient

from dlite_entities_service.config import CONFIG

MONGO_CLIENT = MongoClient(CONFIG.mongo_uri)
MONGO_DB = MONGO_CLIENT.dlite

ENTITIES_COLLECTION = MONGO_DB.entities
