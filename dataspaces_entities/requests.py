"""Custom FastAPI/Starlette Requests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import yaml
from fastapi import Request, Response
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from pydantic import ValidationError
from s7 import get_entity

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Coroutine, Sequence
    from enum import Enum
    from typing import Any

    from fastapi import IncEx, params
    from fastapi.datastructures import DefaultPlaceholder
    from pydantic_core import ErrorDetails
    from s7 import SOFT7Entity
    from starlette.routing import BaseRoute


logger = logging.getLogger(__name__)


class YamlRequest(Request):
    """Custom request class for SOFT Entities requests supporting both JSON and YAML bodies."""

    async def yaml(self) -> list[Any]:
        """Parse and return the request body as YAML."""
        if not hasattr(self, "_yaml"):
            body = await self.body()
            self._yaml = list(yaml.safe_load_all(body))

        return self._yaml

    async def _raw_to_entities(
        self, raw_entities: list[dict[str, Any]] | dict[str, Any]
    ) -> list[SOFT7Entity]:
        """Convert raw entities to SOFT7Entity instances.

        Expect the raw entities to be a list of dictionaries or a single dictionary.
        It should always be equivalent to a single YAML document (if parsed as YAML).

        Note, if only `pydantic.ValidationError`s are raised, the error messages are combined into a single
        `pydantic.ValidationError` instance, which is then raised.

        """
        errors: list[ValidationError] = []
        parsed_entities: list[SOFT7Entity] = []

        if isinstance(raw_entities, list):
            if not all(isinstance(raw_entity, dict) for raw_entity in raw_entities):
                raise TypeError("Invalid entities provided. Cannot be parsed as dicts.")

            for raw_entity in raw_entities:
                try:
                    parsed_entities.append(get_entity(raw_entity))
                except ValidationError as exc:
                    errors.append(exc)

        elif isinstance(raw_entities, dict):
            try:
                parsed_entities = [get_entity(raw_entities)]
            except ValidationError as exc:
                errors.append(exc)

        else:
            raise TypeError("Invalid entities provided. Cannot be parsed individually as dicts.")

        # Handle any caught ValidationErrors
        if errors:
            line_errors: list[ErrorDetails] = []
            for validation_error in errors:
                line_errors.extend(validation_error.errors())

            raise ValidationError.from_exception_data(
                title=errors[0].title,
                # Arg-type is ignored, since line_errors expects `list[InitErrorDetails]`,
                # which is a sub-set of `list[ErrorDetails]`.
                line_errors=line_errors,  # type: ignore[arg-type]
                input_type="python",
                hide_input=False,
            )

        # Return entities, since no errors were found
        return parsed_entities

    async def parse_entities(self) -> list[SOFT7Entity] | SOFT7Entity:
        """Parse and return the request body as SOFT entities."""
        # Parse entities based on the Content-Type header
        for content_type in self.headers.getlist("Content-Type"):
            # Handle YAML (Content-Type: application/yaml)
            if "application/yaml" in content_type or content_type.endswith("+yaml"):
                parsed_entities: list[SOFT7Entity] = []

                for yaml_doc in await self.yaml():
                    parsed_entities.extend(await self._raw_to_entities(yaml_doc))

                return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

            if "application/json" in content_type or content_type.endswith("+json"):
                parsed_entities = await self._raw_to_entities(await self.json())
                return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

        # Could not determine body content type from headers
        # Will instead check the "Content-Type" header.
        # If it does not exist, try parsing the body using the YAML parser (as it is a super-set of JSON
        # and will therefore work for both).
        # If it does exist, raise an error, as the correct content type is not specified.
        if "Content-Type" not in self.headers:
            logger.warning(
                "No 'Content-Type' header found in the request. Falling back to parsing body using the "
                "YAML parser as it is a super-set of JSON (expecting content to be either JSON or YAML)."
            )
            parsed_entities = []

            for yaml_doc in await self.yaml():
                parsed_entities.extend(await self._raw_to_entities(yaml_doc))

            return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

        raise ValueError("Could not parse the entities from the request body.")

    async def parse_partial_entities(self) -> list[dict[str, Any]] | dict[str, Any]:
        """Parse and return the request body as partial SOFT entities."""
        # Parse entities based on the Content-Type header
        for content_type in self.headers.getlist("Content-Type"):
            # Handle YAML (Content-Type: application/yaml)
            if "application/yaml" in content_type or content_type.endswith("+yaml"):
                parsed_entities: list[dict[str, Any]] = []

                for yaml_doc in await self.yaml():
                    if isinstance(yaml_doc, dict):
                        parsed_entities.append(yaml_doc)
                    elif isinstance(yaml_doc, list) and all(
                        isinstance(raw_entity, dict) for raw_entity in yaml_doc
                    ):
                        parsed_entities.extend(yaml_doc)
                    else:
                        raise TypeError(
                            "Invalid (partial) entities provided. Cannot be parsed individually as dicts."
                        )

                return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

            if "application/json" in content_type or content_type.endswith("+json"):
                parsed_entities = await self.json()
                if not isinstance(parsed_entities, dict) or (
                    isinstance(parsed_entities, list)
                    and not all(isinstance(raw_entity, dict) for raw_entity in parsed_entities)
                ):
                    raise TypeError(
                        "Invalid (partial) entities provided. Cannot be parsed individually as dicts."
                    )

                return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

        # Could not determine body content type from headers
        # Will instead check the "Content-Type" header.
        # If it does not exist, try parsing the body using the YAML parser (as it is a super-set of JSON
        # and will therefore work for both).
        # If it does exist, raise an error, as the correct content type is not specified.
        if "Content-Type" not in self.headers:
            logger.warning(
                "No 'Content-Type' header found in the request. Falling back to parsing body using the "
                "YAML parser as it is a super-set of JSON (expecting content to be either JSON or YAML)."
            )
            parsed_entities = []

            for yaml_doc in await self.yaml():
                if isinstance(yaml_doc, dict):
                    parsed_entities.append(yaml_doc)
                elif isinstance(yaml_doc, list) and all(
                    isinstance(raw_entity, dict) for raw_entity in yaml_doc
                ):
                    parsed_entities.extend(yaml_doc)
                else:
                    raise TypeError(
                        "Invalid (partial) entities provided. Cannot be parsed individually as dicts."
                    )

            return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

        raise ValueError("Could not parse the (partial) entities from the request body.")


class YamlRoute(APIRoute):
    """Custom route class for YAML requests."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """Return the route handler."""
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            """Custom route handler supporting YAML body requests."""
            request = YamlRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler

    # Override __init__ to extend the OpenAPI specification with YAML support
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = Default(None),
        status_code: int | None = None,
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        name: str | None = None,
        methods: set[str] | list[str] | None = None,
        operation_id: str | None = None,
        response_model_include: IncEx | None = None,
        response_model_exclude: IncEx | None = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
        dependency_overrides_provider: Any | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[[APIRoute], str] | DefaultPlaceholder = Default(
            generate_unique_id
        ),
    ) -> None:
        # Ensure that the Route only extends the OpenAPI spec for methods that expect an entities body.
        body_entities_methods = {"POST", "PUT", "PATCH"}

        if methods and any(_ in methods for _ in body_entities_methods):
            is_patch = "PATCH" in methods

            # Manually extend OpenAPI specification's request body for the Route.
            # This is to explicitly support multiple content types (application/json and application/yaml).
            # Extend the OpenAPI specification with YAML support
            openapi_extra = openapi_extra or {}

            # This is equivalent to the Python type: `list[SOFT7Entity] | SOFT7Entity`
            entities_type_schema = (
                [
                    {
                        "type": "array",
                        "items": "object",
                    },
                    "object",
                ]
                if is_patch
                else [
                    {"type": "array", "items": {"$ref": "#/components/schemas/SOFT7Entity"}},
                    {"$ref": "#/components/schemas/SOFT7Entity"},
                ]
            )

            openapi_extra["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {"schema": {"anyOf": entities_type_schema, "title": "Entities"}},
                    "application/yaml": {"schema": {"anyOf": entities_type_schema, "title": "Entities"}},
                },
            }

            if not is_patch:
                # Manually add 422 - Validation Error to the OpenAPI documentation.
                # This is because it is not automatically added when using the `request` parameter
                # straight up. Which is how this Route should always be used.
                responses = responses or {}
                if 422 not in responses or "422" not in responses:
                    responses[422] = {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                            }
                        },
                    }

        super().__init__(
            path,
            endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            name=name,
            methods=methods,
            operation_id=operation_id,
            response_model_include=response_model_include,
            response_model_exclude=response_model_exclude,
            response_model_by_alias=response_model_by_alias,
            response_model_exclude_unset=response_model_exclude_unset,
            response_model_exclude_defaults=response_model_exclude_defaults,
            response_model_exclude_none=response_model_exclude_none,
            include_in_schema=include_in_schema,
            response_class=response_class,
            dependency_overrides_provider=dependency_overrides_provider,
            callbacks=callbacks,
            openapi_extra=openapi_extra,
            generate_unique_id_function=generate_unique_id_function,
        )
