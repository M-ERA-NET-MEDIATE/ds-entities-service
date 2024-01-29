"""Service-specific exceptions."""
from __future__ import annotations

from pymongo.errors import InvalidDocument, PyMongoError

BackendError = (PyMongoError, InvalidDocument)
"""Any backend error exception."""
