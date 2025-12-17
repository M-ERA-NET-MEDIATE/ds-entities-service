"""FastAPI exception handlers."""

from __future__ import annotations

import logging
import traceback
from typing import TYPE_CHECKING

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from dataspaces_entities.config import get_config
from dataspaces_entities.exceptions import DSEntitiesAPIException
from dataspaces_entities.models import Error, ErrorResponse

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Iterable

LOGGER = logging.getLogger(__name__)


def general_exception(
    request: Request,
    exc: Exception,
    status_code: int = 500,  # A status_code in `exc` will take precedence
    errors: list[Error] | None = None,
) -> JSONResponse:
    """Handle an exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.
        status_code: The returned HTTP status code for the error response.
        errors: List of error resources.

    Returns:
        A JSON HTTP response.

    """
    debug_info = {}
    if get_config().debug:
        tb = "".join(traceback.format_exception(type(exc), value=exc, tb=exc.__traceback__))
        LOGGER.error("Traceback:\n%s", tb)
        debug_info["_py_traceback"] = tb

    title = str(getattr(exc, "title", exc.__class__.__name__))
    http_response_code = int(getattr(exc, "status_code", status_code))
    detail = str(getattr(exc, "detail", exc))

    LOGGER.error(
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
    exc: HTTPException | DSEntitiesAPIException | RequestValidationError,
) -> JSONResponse:
    """Handle a general HTTP Exception from FastAPI/Starlette and any from DataSpaces-Entities

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
    return general_exception(request, exc)


def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle a general Pydantic validation error

    The pydantic `ValidationError` usually contains a list of errors.
    This function extracts them and wraps them in the
    [`Error`][dataspaces_entities.models.Error] pydantic model.

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    """
    status = 500
    title = "ValidationError"
    errors = set()
    for error in exc.errors():
        extra = {}
        if get_config().debug:
            extra = {
                "ctx": error["ctx"],
                "input": error["input"],
            }
        errors.add(
            Error(
                title=title,
                status=status,
                detail=error["msg"],
                loc="/" + "/".join([str(_) for _ in error["loc"]]),
                type=error["type"],
                **extra,
            )
        )
    return general_exception(request, exc, status_code=status, errors=list(errors))


def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    """Handle a standard NotImplementedError Python exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through
        [`general_exception()`][dataspaces_entities.exception_handlers.general_exception].

    """
    status = 501
    title = "NotImplementedError"
    detail = str(exc)
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
    (RequestValidationError, http_exception_handler),
    (ValidationError, validation_exception_handler),  # type: ignore[list-item]
    (NotImplementedError, not_implemented_handler),  # type: ignore[list-item]
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
