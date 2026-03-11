"""Exceptions for the DataSpaces-Entities API."""

from __future__ import annotations

from dataspaces_utils.fastapi.exceptions import DSAPIException
from fastapi import status


class DSEntitiesGeneralException(DSAPIException):
    """General exception for the DataSpaces-Entities API."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    title = "General Server Error"


class EntityExists(DSEntitiesGeneralException):
    """Entity already exists."""

    status_code = status.HTTP_409_CONFLICT
    title = "Entity Already Exists"

    def __init__(
        self,
        entity_id: str,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """Initialize the exception with the entity ID."""
        detail = detail if detail else f"Entity already exists: {entity_id}"
        super().__init__(detail=detail, headers=headers)
        self.resource_identifier = entity_id


class InvalidEntityError(DSEntitiesGeneralException):
    """Invalid entity error."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    title = "Invalid Entity"


class WriteError(DSEntitiesGeneralException):
    """Error writing entity to backend."""

    status_code = status.HTTP_502_BAD_GATEWAY
    title = "Internal Write Error"


class RequestError(DSEntitiesGeneralException):
    """Error with the client request."""

    status_code = status.HTTP_400_BAD_REQUEST
    title = "Bad Request"


class RaceConditionError(DSEntitiesGeneralException):
    """Race condition error."""

    status_code = status.HTTP_409_CONFLICT
    title = "Race Condition Error"
