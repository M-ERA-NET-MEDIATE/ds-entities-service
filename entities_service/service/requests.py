"""Custom FastAPI/Starlette Requests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import yaml
from fastapi import Request, Response
from fastapi.routing import APIRoute
from pydantic import ValidationError

from entities_service.models import soft_entity

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from typing import Any

    from pydantic_core import ErrorDetails

    from entities_service.models import VersionedSOFTEntity


LOGGER = logging.getLogger(__name__)


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
    ) -> list[VersionedSOFTEntity]:
        """Convert raw entities to VersionedSOFTEntity instances.

        Expect the raw entities to be a list of dictionaries or a single dictionary.
        It should always be equivalent to a single YAML document (if parsed as YAML).
        """
        if isinstance(raw_entities, list):
            if not all(isinstance(raw_entity, dict) for raw_entity in raw_entities):
                raise TypeError("Invalid entities provided. Cannot be parsed as dicts.")

            parsed_entities = [soft_entity(return_errors=True, **raw_entity) for raw_entity in raw_entities]

        elif isinstance(raw_entities, dict):
            parsed_entities = [soft_entity(return_errors=True, **raw_entities)]

        else:
            raise TypeError("Invalid entities provided. Cannot be parsed as dicts.")

        # Handle any ValidationErrors
        errors: list[ValidationError] = []
        for parsed_entity in parsed_entities:
            if isinstance(parsed_entity, list):
                # It is not an entity, but rather a list of ValidationErrors
                errors.extend(parsed_entity)

        if errors:
            line_errors: list[ErrorDetails] = []
            for validation_errors in errors:
                line_errors.extend(validation_errors.errors())

            raise ValidationError.from_exception_data(
                title=errors[0].title,
                # Arg-type is ignored, since line_errors expects `list[InitErrorDetails]`,
                # which is a sub-set of `list[ErrorDetails]`.
                line_errors=line_errors,  # type: ignore[arg-type]
                input_type="python",
                hide_input=False,
            )

        # Return entities, since no errors were found
        # Ignoring mypy's warning here, as we _know_ that parsed_entities is a list of only
        # VersionedSOFTEntity objects.
        return parsed_entities  # type: ignore[return-value]

    async def parse_entities(self) -> list[VersionedSOFTEntity] | VersionedSOFTEntity:
        """Parse and return the request body as SOFT entities."""
        # Parse entities based on the Content-Type header
        for content_type in self.headers.getlist("Content-Type"):
            # Handle YAML (Content-Type: application/yaml)
            if "application/yaml" in content_type or content_type.endswith("+yaml"):
                yaml_docs = await self.yaml()
                parsed_entities: list[VersionedSOFTEntity] = []

                for yaml_doc in yaml_docs:
                    if not isinstance(yaml_doc, dict):
                        raise TypeError("Invalid entities provided. Cannot be parsed as dicts.")
                    parsed_entities.extend(await self._raw_to_entities(yaml_doc))

                return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

            if "application/json" in content_type or content_type.endswith("+json"):
                return await self._raw_to_entities(await self.json())

        # Could not determine body content type from headers
        # Will instead check the "Content-Type" header.
        # If it does not exist, try parsing the body using the YAML parser (as it is a super-set of JSON
        # and will therefore work for both).
        # If it does exist, raise an error, as the correct content type is not specified.
        if "Content-Type" not in self.headers:
            LOGGER.warning(
                "No 'Content-Type' header found in the request. Falling back to parsing body using the "
                "YAML parser as it is a super-set of JSON (expecting content to be either JSON or YAML)."
            )
            yaml_docs = await self.yaml()
            parsed_entities = []

            for yaml_doc in yaml_docs:
                if not isinstance(yaml_doc, dict):
                    raise TypeError("Invalid entities provided. Cannot be parsed as dicts.")
                parsed_entities.extend(await self._raw_to_entities(yaml_doc))

            return parsed_entities[0] if len(parsed_entities) == 1 else parsed_entities

        raise ValueError("Could not parse entities from the request body.")


class YamlRoute(APIRoute):
    """Custom route class for YAML requests."""

    def get_route_handler(self) -> Callable:
        """Return the route handler."""
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            """Custom route handler supporting YAML body requests."""
            request = YamlRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
