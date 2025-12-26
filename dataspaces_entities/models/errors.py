"""Data models representing API errors."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class Error(BaseModel):
    """Data model representing an API error."""

    model_config = ConfigDict(extra="allow")

    title: Annotated[
        str,
        Field(
            title="Title",
            description="The error title.",
        ),
    ]

    status: Annotated[
        int,
        Field(
            title="Status",
            description="The HTTP status code.",
        ),
    ]

    detail: Annotated[
        str,
        Field(
            title="Detail",
            description="The error detail message.",
        ),
    ]


class ErrorResponse(BaseModel):
    """Error response model."""

    meta: Annotated[
        dict[str, Any],
        Field(
            title="Meta",
            description="The error response metadata.",
        ),
    ]

    errors: Annotated[
        list[Error],
        Field(
            title="Errors",
            description="List of the errors.",
        ),
    ]
