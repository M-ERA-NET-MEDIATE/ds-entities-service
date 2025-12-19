"""Exceptions for the DataSpaces-Entities API."""

from __future__ import annotations

from abc import ABC

from fastapi import status


class DSEntitiesAPIException(Exception, ABC):
    """Base exception for the DataSpaces-Entities API.

    This abstract class can be subclassed to define HTTP responses with the desired status codes,
    and detailed error strings to represent in the error response.

    This class closely follows the FastAPI/Starlette `HTTPException` without requiring it as a
    dependency, so that such errors can also be raised from within client code.

    Attributes:
        title: A descriptive title for this exception.
        status_code: The HTTP status code accompanying this exception.
        detail: An optional string containing the details of the error.
        headers: An optional mapping of HTTP headers to include with the response.

    """

    title: str = ""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str | None = None
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None, headers: dict[str, str] | None = None) -> None:
        """Initialize the exception with an optional detail message."""
        if not self.title:
            self.title = self.__class__.__name__

        self.detail = detail
        self.headers = headers

    def __str__(self) -> str:
        return self.detail if self.detail is not None else self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code!r}, detail={self.detail!r})"


class DSEntitiesGeneralException(DSEntitiesAPIException):
    """General exception for the DataSpaces-Entities API."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    title = "General Server Error"


class EntityNotFound(DSEntitiesGeneralException):
    """Entity not found."""

    status_code = status.HTTP_404_NOT_FOUND
    title = "Entity Not Found"

    def __init__(
        self,
        entity_id: str,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """Initialize the exception with the entity name."""
        detail = detail if detail else f"Entity not found: {entity_id}"
        super().__init__(detail=detail, headers=headers)
        self.entity_id = entity_id


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
        self.entity_id = entity_id


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

    title = "Race Condition Error"


ERRORS_WITH_STATUS_CODES: list[type[DSEntitiesAPIException]] = [
    DSEntitiesGeneralException,
    EntityNotFound,
    EntityExists,
    InvalidEntityError,
    WriteError,
    RequestError,
]
"""List of exceptions that should be returned with an HTTP status code.

These exceptions represent errors with unique status codes.

This list is used for OpenAPI documentation generation.
"""
