"""FastAPI exception handlers."""

from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING

from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from dataspaces_entities.config import get_config
from dataspaces_entities.exceptions import DSEntitiesAPIException
from dataspaces_entities.models import Error, ErrorResponse

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Iterable
    from typing import Any

logger = logging.getLogger(__name__)


def general_exception(
    request: Request,
    exc: Exception,
    status_code: int = http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    errors: list[Error] | None = None,
) -> JSONResponse:
    """Handle an exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.
        status_code: The returned HTTP status code for the error response.
            A status code in the exception will override this value.
        errors: List of error resources.

    Returns:
        A JSON HTTP response.

    """
    debug_info = {}
    if get_config().debug:
        tb = "".join(traceback.format_exception(type(exc), value=exc, tb=exc.__traceback__))
        logger.error("Traceback:\n%s", tb)
        debug_info["_py_traceback"] = tb

    title = str(getattr(exc, "title", exc.__class__.__name__))
    http_response_code = int(getattr(exc, "status_code", status_code))
    detail = str(getattr(exc, "detail", exc))

    logger.error(
        "HTTP %d: %s\n%s",
        http_response_code,
        title,
        detail,
    )

    response = ErrorResponse(
        meta={
            "url": str(request.url),
            **debug_info,
        },
        errors=errors or [Error(title=title, status=http_response_code, detail=detail)],
    )

    return JSONResponse(
        status_code=http_response_code,
        content=jsonable_encoder(response),
    )


def http_exception_handler(
    request: Request,
    exc: HTTPException | DSEntitiesAPIException,
) -> JSONResponse:
    """Handle a general HTTP Exception from FastAPI/Starlette and any from DataSpaces-Entities

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    """
    return general_exception(request, exc)


def validation_exception_handler(
    request: Request, exc: ValidationError | RequestValidationError
) -> JSONResponse:
    """Handle a general Pydantic validation error

    The pydantic `ValidationError` usually contains a list of errors.
    This function extracts them and wraps them in the
    [`Error`][dataspaces_entities.models.Error] pydantic model.

    `RequestValidationError` is a specialization of a general pydantic `ValidationError`.
    Pass-through directly to
    [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    """
    status = http_status.HTTP_422_UNPROCESSABLE_CONTENT
    title = exc.title if hasattr(exc, "title") else exc.__class__.__name__

    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        logger.debug("error: %s", error)
        extra = {}
        if get_config().debug:
            extra = {"input": error["input"]}
            if "ctx" in error:
                extra["ctx"] = error["ctx"]
            if hasattr(exc, "body"):
                body = None
                if hasattr(exc.body, "model_dump_json"):
                    body = exc.body.model_dump_json()
                else:
                    try:
                        body = jsonable_encoder(exc.body)
                    except Exception:
                        logger.exception("Failed to JSON encode body, will not add it to error details.")

                if body:
                    extra["body"] = body

        new_error = {
            "title": title,
            "status": status,
            "detail": error["msg"],
            "loc": "/" + "/".join([str(_) for _ in error["loc"]]),
            "type": error["type"],
            **extra,
        }

        if new_error in errors:
            continue

        errors.append(new_error)

    return general_exception(
        request,
        exc,
        status_code=status,
        errors=[Error.model_validate(error) for error in errors],
    )


def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    """Handle a standard NotImplementedError Python exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    """
    status = http_status.HTTP_501_NOT_IMPLEMENTED
    title = "NotImplementedError"
    detail = str(exc)
    return general_exception(
        request,
        exc,
        status_code=status,
        errors=[Error(title=title, status=status, detail=detail)],
    )


def permissions_exception_handler(request: Request, exc: PermissionError) -> JSONResponse:
    """Handle a standard PermissionError Python exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces.exception_handlers.general_exception].

    """
    status = http_status.HTTP_403_FORBIDDEN
    title = "Forbidden"
    detail = str(exc) if get_config().debug else title
    return general_exception(
        request,
        exc,
        status_code=status,
        errors=[Error(title=title, status=status, detail=detail)],
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all Python Exceptions not handled by other exception handlers

    Pass-through directly to
    [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    """
    return general_exception(request, exc)


DS_ENTITIES_EXCEPTIONS: Iterable[
    tuple[
        type[Exception],
        Callable[[Request, Exception], JSONResponse],
    ]
] = [
    (HTTPException, http_exception_handler),
    (DSEntitiesAPIException, http_exception_handler),
    (RequestValidationError, validation_exception_handler),
    (ValidationError, validation_exception_handler),
    (NotImplementedError, not_implemented_handler),  # type: ignore[list-item]
    (PermissionError, permissions_exception_handler),  # type: ignore[list-item]
    (Exception, general_exception_handler),
]
"""A tuple of all pairs of exceptions and handler functions that allow for appropriate responses to
be returned in certain scenarios.

To use these in FastAPI app code:

```python
from fastapi import FastAPI

app = FastAPI()
for exception, handler in DS_ENTITIES_EXCEPTIONS:
    app.add_exception_handler(exception, handler)
```

"""
