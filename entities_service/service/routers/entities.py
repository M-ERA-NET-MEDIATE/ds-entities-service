"""Entities endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from dataspaces_auth.fastapi import has_role
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import Field, ValidationError, conlist
from s7 import SOFT7Entity

from entities_service.models import URI_REGEX, DSAPIRole, HTTPError
from entities_service.service.backend import get_backend
from entities_service.service.config import CONFIG
from entities_service.service.requests import YamlRequest, YamlRoute
from entities_service.service.utils import get_identity

LOGGER = logging.getLogger(__name__)

ROUTER = APIRouter(
    prefix="/entities",
    tags=["Entities"],
    route_class=YamlRoute,
)

URIStrictType = Annotated[str, Field(pattern=URI_REGEX.pattern)]
EmptyList: type[list[Any]] = conlist(Any, min_length=0, max_length=0)  # type: ignore[arg-type]


@ROUTER.get(
    "/",
    response_model=list[SOFT7Entity] | SOFT7Entity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_READ))],
    summary="Retrieve one or more Entity.",
    response_description="Retrieved Entity or Entities.",
    responses={404: {"description": "Entites not found", "model": HTTPError}},
)
async def get_entities(
    identities: Annotated[
        list[URIStrictType] | None,
        Query(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to retrieve.",
            alias="id",
        ),
    ] = None,
    properties: Annotated[
        list[str] | None,
        Query(
            title="Entity property",
            description="A property the retrieved entity/-ies may possess.",
            min_length=1,
            alias="prop",
        ),
    ] = None,
    dimensions: Annotated[
        list[str] | None,
        Query(
            title="Entity dimension",
            description="A dimension the retrieved entity/-ies may possess.",
            min_length=1,
            alias="dim",
        ),
    ] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Retrieve one or more Entities.

    An inclusive search will be performed based the provided identities, properties,
    and dimensions. If no search parameters are provided, all entities will be
    retrieved.
    """
    backend = get_backend()

    entities = list(
        backend.search(by_identity=identities, by_properties=properties, by_dimensions=dimensions)
    )

    if entities:
        if len(entities) == 1:
            return entities[0]
        return entities

    LOGGER.error(
        "Could not find entities:\n  identities=%s\n  properties=%s\n  dimensions=%s",
        ", ".join(identities) if identities else "None",
        ", ".join(properties) if properties else "None",
        ", ".join(dimensions) if dimensions else "None",
    )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Could not find entities: identities={identities}",
    )


@ROUTER.post(
    "/",
    response_model=list[SOFT7Entity] | SOFT7Entity | None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_WRITE))],
    summary="Create one or more Entities.",
    response_description="Created Entity or Entities.",
    responses={
        200: {"description": "There are no Entities to replace or create", "model": EmptyList},
        502: {"description": "Internal write error", "model": HTTPError},
    },
)
async def create_entities(
    request: YamlRequest,
    response: Response,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Create one or more Entities."""
    # Parse entities from request
    try:
        entities = await request.parse_entities()
    except ValidationError as err:
        LOGGER.error("Could not validate entities from request.")
        LOGGER.exception(err)
        raise RequestValidationError(errors=err.errors(), body=await request.body()) from err
    except (ValueError, TypeError) as err:
        LOGGER.error("Could not parse entities from request.")
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid entities provided. Cannot parse request.",
        ) from err

    # Check client-sent content
    if isinstance(entities, list):
        # Check if there are any entities to create
        if not entities:
            response.status_code = status.HTTP_200_OK
            return []
    else:
        entities = [entities]

    write_fail_exception = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Could not create entit"
            "{suffix} with identit{suffix}: {identities}".format(
                suffix="y" if len(entities) == 1 else "ies",
                identities=", ".join(get_identity(entity) for entity in entities),
            )
        ),
    )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    try:
        created_entities = entities_backend.create(entities)
    except entities_backend.write_access_exception as err:
        LOGGER.error(
            "Could not create entities: identities=[%s]",
            ", ".join(get_identity(entity) for entity in entities),
        )
        LOGGER.exception(err)
        raise write_fail_exception from err

    if (
        created_entities is None
        or (len(entities) == 1 and isinstance(created_entities, list))
        or (len(entities) > 1 and not isinstance(created_entities, list))
    ):
        raise write_fail_exception

    return created_entities


@ROUTER.put(
    "/",
    response_model=list[SOFT7Entity] | SOFT7Entity | None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_EDIT))],
    summary="Replace and/or create one or more Entities.",
    response_description="Created (not replaced) Entity or Entities.",
    responses={
        200: {"description": "There are no Entities to replace or create", "model": EmptyList},
        204: {"description": "Replaced (not created) Entity or Entitites"},
        502: {"description": "Internal write error", "model": HTTPError},
    },
)
async def update_entities(
    request: YamlRequest,
    response: Response,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Replace and/or create one or more Entities."""
    # Parse entities from request
    try:
        entities = await request.parse_entities()
    except ValidationError as err:
        LOGGER.error("Could not validate entities from request.")
        LOGGER.exception(err)
        raise RequestValidationError(errors=err.errors(), body=await request.body()) from err
    except (ValueError, TypeError) as err:
        LOGGER.error("Could not parse entities from request.")
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid entities provided. Cannot parse request.",
        ) from err

    # Check client-sent content
    if isinstance(entities, list):
        # Check if there are any entities to update
        if not entities:
            response.status_code = status.HTTP_200_OK
            return []
    else:
        entities = [entities]

    write_fail_exception = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Could not put/update entit"
            "{suffix} with identit{suffix}: {identities}".format(
                suffix="y" if len(entities) == 1 else "ies",
                identities=", ".join(get_identity(entity) for entity in entities),
            )
        ),
    )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    new_entities = [entity for entity in entities if get_identity(entity) not in entities_backend]

    if new_entities:
        try:
            created_entities = entities_backend.create(new_entities)
        except entities_backend.write_access_exception as err:
            LOGGER.error(
                "Could not create entities: identities=[%s]",
                ", ".join(get_identity(entity) for entity in new_entities),
            )
            LOGGER.exception(err)
            raise write_fail_exception from err

        if (
            created_entities is None
            or (len(new_entities) == 1 and isinstance(created_entities, list))
            or (len(new_entities) > 1 and not isinstance(created_entities, list))
        ):
            raise write_fail_exception

    # Update existing entities
    for entity in entities:
        if entity in new_entities:
            continue

        if (identity := get_identity(entity)) in entities_backend:
            try:
                entities_backend.update(identity, entity)
            except entities_backend.write_access_exception as err:
                LOGGER.error(
                    "Could not update entities: identities=[%s]",
                    ", ".join(get_identity(entity) for entity in entities),
                )
                LOGGER.error("Error happened when updating entity: identity=%s", identity)
                LOGGER.exception(err)
                raise write_fail_exception from err

    if new_entities:
        return created_entities

    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@ROUTER.patch(
    "/",
    response_model=None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_EDIT))],
    summary="Update one or more Entities.",
    response_description="Updated Entity or Entities.",
    responses={
        200: {"description": "There are no Entities to update", "model": EmptyList},
        502: {"description": "Internal write error", "model": HTTPError},
    },
)
async def patch_entities(request: YamlRequest, response: Response) -> list[Any] | None:
    """Update one or more Entities."""
    # Parse entities from request
    try:
        entities = await request.parse_partial_entities()
    except (ValueError, TypeError) as err:
        LOGGER.error("Could not parse (partial) entities from request.")
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid (partial) entities provided. Cannot parse request.",
        ) from err

    # Check client-sent content
    if isinstance(entities, list):
        # Check if there are any entities to update
        if not entities:
            response.status_code = status.HTTP_200_OK
            return []
    else:
        entities = [entities]

    write_fail_exception = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Could not patch/update entit"
            "{suffix} with identit{suffix}: {identities}".format(
                suffix="y" if len(entities) == 1 else "ies",
                identities=", ".join(get_identity(entity) for entity in entities),
            )
        ),
    )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    # First, check all entities already exist
    non_existing_entities = [entity for entity in entities if get_identity(entity) not in entities_backend]
    if non_existing_entities:
        LOGGER.error(
            "Cannot patch non-existent entities: identities=[%s]",
            ", ".join(get_identity(entity) for entity in non_existing_entities),
        )
        raise write_fail_exception

    for entity in entities:
        try:
            entities_backend.update(get_identity(entity), entity)
        except entities_backend.write_access_exception as err:
            LOGGER.error(
                "Could not update entities: identities=[%s]",
                ", ".join(get_identity(entity) for entity in entities),
            )
            LOGGER.error("Error happened when updating entity: identity=%s", get_identity(entity))
            LOGGER.exception(err)
            raise write_fail_exception from err

    return None


@ROUTER.delete(
    "/",
    response_model=list[URIStrictType] | URIStrictType,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_DELETE))],
    summary="Delete one or more Entities.",
    response_description="Deleted Entity identity or identities.",
    responses={
        400: {"description": "No Entity identities provided", "model": HTTPError},
        502: {"description": "Internal write error", "model": HTTPError},
    },
)
async def delete_entities(
    identities_body: Annotated[
        list[URIStrictType] | URIStrictType | None,
        Body(
            title="Entity identity",
            description="The identity/-ies (URI/IRI) of the entity/-ies to delete.",
        ),
    ] = None,
    identities_query: Annotated[
        list[URIStrictType] | None,
        Query(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to delete.",
            alias="id",
        ),
    ] = None,
) -> list[URIStrictType] | URIStrictType:
    """Delete one or more Entities."""
    identities: set[URIStrictType] = set()

    if isinstance(identities_body, str):
        identities.add(identities_body)
    elif isinstance(identities_body, list):
        identities.update(identities_body)

    if isinstance(identities_query, list):
        identities.update(identities_query)

    if not identities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Entity identities provided.",
        )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    try:
        entities_backend.delete(identities)
    except entities_backend.write_access_exception as err:
        LOGGER.error(
            "Could not delete entities: identity=%s",
            ", ".join(str(identity) for identity in identities),
        )
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Could not delete entit"
                "{suffix} with identit{suffix}: {identities}".format(
                    suffix="y" if len(identities) == 1 else "ies",
                    identities=", ".join(str(identity) for identity in identities),
                )
            ),
        ) from err

    if len(identities) == 1:
        return identities.pop()

    return sorted(identities)
