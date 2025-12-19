"""Entities endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any, get_args

from dataspaces_auth.fastapi import has_role
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Query,
    Response,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, conlist
from s7 import SOFT7Entity
from s7.pydantic_models.soft7_entity import SOFT7IdentityURIType

from dataspaces_entities.backend import get_backend
from dataspaces_entities.config import get_config
from dataspaces_entities.exceptions import (
    EntityNotFound,
    InvalidEntityError,
    RequestError,
    WriteError,
)
from dataspaces_entities.models import DSAPIRole
from dataspaces_entities.requests import YamlRequest, YamlRoute
from dataspaces_entities.utils import generate_error_display_ids, get_identity

logger = logging.getLogger(__name__)

ROUTER = APIRouter(
    prefix="/entities",
    tags=["Entities"],
    route_class=YamlRoute,
)

EmptyList: type[list[Any]] = conlist(Any, min_length=0, max_length=0)  # type: ignore[arg-type]


@ROUTER.get(
    "/",
    response_model=list[SOFT7Entity] | SOFT7Entity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_READ))],
    summary="Retrieve one or more Entity.",
    response_description="Retrieved Entity or Entities.",
)
async def get_entities(
    identities: Annotated[
        list[SOFT7IdentityURIType] | None,
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
        backend.search(by_identities=identities, by_properties=properties, by_dimensions=dimensions)
    )

    if entities:
        if len(entities) == 1:
            return entities[0]
        return entities

    logger.error(
        "Could not find entities:\n  identities=%s\n  properties=%s\n  dimensions=%s",
        str(identities) if identities else "None",
        ", ".join(properties) if properties else "None",
        ", ".join(dimensions) if dimensions else "None",
    )

    raise EntityNotFound(
        entity_id=", ".join(str(identity) for identity in identities) if identities else "see detail",
        detail=(
            f"Could not find entities:"
            f"{' identities=' + ', '.join(str(identity) for identity in identities) if identities else ''}"
            f"{' properties=' + ', '.join(properties) if properties else ''}"
            f"{' dimensions=' + ', '.join(dimensions) if dimensions else ''}"
        ),
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
        logger.exception("Could not validate entities from request.")
        raise RequestValidationError(errors=err.errors(), body=await request.body()) from err
    except (ValueError, TypeError) as err:
        logger.exception("Could not parse entities from request.")
        raise InvalidEntityError("Invalid entities provided. Cannot parse request.") from err

    # Check client-sent content
    if isinstance(entities, list):
        # Check if there are any entities to create
        if not entities:
            response.status_code = status.HTTP_200_OK
            return []
    else:
        entities = [entities]

    config = get_config()

    entities_backend = get_backend(config.backend)

    entity_ids = [get_identity(entity) for entity in entities]

    write_fail_exception = WriteError(
        "Could not create entit"
        "{suffix} with identit{suffix}: {identities}".format(
            suffix="y" if len(entities) == 1 else "ies",
            identities=", ".join(generate_error_display_ids(entity_ids=entity_ids)),
        )
    )

    try:
        created_entities = entities_backend.create(entities)
    except entities_backend.write_access_exception as err:
        logger.exception(
            "Could not create entities: identities=[%s]",
            ", ".join(entity_ids),
        )
        raise write_fail_exception from err

    if (
        created_entities is None
        or (len(entities) == 1 and isinstance(created_entities, list))
        or (len(entities) > 1 and isinstance(created_entities, dict))
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
        logger.exception("Could not validate entities from request.")
        raise RequestValidationError(errors=err.errors(), body=await request.body()) from err
    except (ValueError, TypeError) as err:
        logger.exception("Could not parse entities from request.")
        raise InvalidEntityError("Invalid entities provided. Cannot parse request.") from err

    # Check client-sent content
    if isinstance(entities, list):
        # Check if there are any entities to update
        if not entities:
            response.status_code = status.HTTP_200_OK
            return []
    else:
        entities = [entities]

    entities_backend = get_backend(get_config().backend)

    entity_ids = [get_identity(entity) for entity in entities]

    write_fail_exception = WriteError(
        "Could not put/update entit"
        "{suffix} with identit{suffix}: {identities}".format(
            suffix="y" if len(entities) == 1 else "ies",
            identities=", ".join(generate_error_display_ids(entity_ids=entity_ids)),
        )
    )

    # Determine which entities need to be created vs. updated
    existing_entities = list(entities_backend.search(by_identities=entity_ids))
    existing_entity_ids = [get_identity(entity) for entity in existing_entities]

    new_entities: list[SOFT7Entity] = []
    entities_to_be_updated: list[SOFT7Entity] = []
    for entity in entities:
        if get_identity(entity) in existing_entity_ids:
            entities_to_be_updated.append(entity)
        else:
            new_entities.append(entity)

    # Update existing entities
    for entity in entities_to_be_updated:
        identity = get_identity(entity)
        try:
            entities_backend.update(identity, entity)
        except entities_backend.write_access_exception as err:
            logger.exception(
                "Could not update entities: identities=[%s]; "
                "was handling a total of %d entities in PUT /entities;"
                "error happened when updating entity: identity=%s",
                ", ".join(existing_entity_ids),
                len(entities),
                identity,
            )
            raise write_fail_exception from err

    if entities_to_be_updated:
        logger.info(
            "Successfully updated existing entities: identities=[%s]",
            ", ".join(get_identity(entity) for entity in entities_to_be_updated),
        )

    # Create new entities
    if new_entities:
        try:
            created_entities = entities_backend.create(new_entities)
        except entities_backend.write_access_exception as err:
            logger.exception(
                "Could not create entities: identities=[%s]; "
                "was handling a total of %d entities in PUT /entities",
                ", ".join(get_identity(entity) for entity in new_entities),
                len(entities),
            )
            raise write_fail_exception from err

        if (
            created_entities is None
            or (len(new_entities) == 1 and isinstance(created_entities, list))
            or (len(new_entities) > 1 and isinstance(created_entities, dict))
        ):
            raise write_fail_exception

        logger.info(
            "Successfully created new entities: identities=[%s]",
            ", ".join(get_identity(entity) for entity in new_entities),
        )

        return created_entities

    # Only updated existing entities
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
    },
)
async def patch_entities(request: YamlRequest, response: Response) -> list[Any] | None:
    """Update one or more Entities."""
    # Parse entities from request
    try:
        entities = await request.parse_partial_entities()
    except (ValueError, TypeError) as err:
        logger.exception("Could not parse (partial) entities from request.")
        raise InvalidEntityError("Invalid (partial) entities provided. Cannot parse request.") from err

    # Check client-sent content
    if isinstance(entities, list):
        # Check if there are any entities to update
        if not entities:
            response.status_code = status.HTTP_200_OK
            return []
    else:
        entities = [entities]

    entities_backend = get_backend(get_config().backend)

    # First, check all entities already exist
    entity_ids = [get_identity(entity) for entity in entities]
    existing_entities = list(entities_backend.search(by_identities=entity_ids))
    existing_entity_ids = {get_identity(entity) for entity in existing_entities}

    if non_existing_entity_ids := list(set(entity_ids) - existing_entity_ids):
        err_msg = "Cannot patch non-existent entities: identities=[{identities}]"

        logger.error(err_msg.format(identities=", ".join(non_existing_entity_ids)))

        raise EntityNotFound(
            entity_id=", ".join(non_existing_entity_ids),
            detail=err_msg.format(
                identities=", ".join(generate_error_display_ids(entity_ids=non_existing_entity_ids))
            ),
        )

    for entity_id, entity in zip(entity_ids, entities, strict=True):
        try:
            entities_backend.update(entity_id, entity)
        except entities_backend.write_access_exception as err:
            logger.exception(
                "Could not update entities: identities=[%s]; "
                "error happened when updating entity: identity=%s",
                ", ".join(entity_ids),
                entity_id,
            )

            raise WriteError(
                "Could not patch/update entit"
                "{suffix} with identit{suffix}: {identities}".format(
                    suffix="y" if len(entities) == 1 else "ies",
                    identities=", ".join(generate_error_display_ids(entity_ids=entity_ids)),
                )
            ) from err

    return None


@ROUTER.delete(
    "/",
    response_model=list[SOFT7IdentityURIType] | SOFT7IdentityURIType,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_role(DSAPIRole.ENTITIES_DELETE))],
    summary="Delete one or more Entities.",
    response_description="Deleted Entity identity or identities.",
)
async def delete_entities(
    identities_body: Annotated[
        list[SOFT7IdentityURIType] | SOFT7IdentityURIType | None,
        Body(
            title="Entity identity",
            description="The identity/-ies (URI/IRI) of the entity/-ies to delete.",
        ),
    ] = None,
    identities_query: Annotated[
        list[SOFT7IdentityURIType] | None,
        Query(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to delete.",
            alias="id",
        ),
    ] = None,
) -> list[SOFT7IdentityURIType] | SOFT7IdentityURIType:
    """Delete one or more Entities."""
    identities: set[SOFT7IdentityURIType] = set()

    if isinstance(identities_body, get_args(SOFT7IdentityURIType)):
        identities.add(identities_body)
    elif isinstance(identities_body, list):
        identities.update(identities_body)

    if isinstance(identities_query, list):
        identities.update(identities_query)

    if not identities:
        raise RequestError("At least one entity identity must be provided to delete entities.")

    entities_backend = get_backend(get_config().backend)

    try:
        entities_backend.delete(identities)
    except entities_backend.write_access_exception as err:
        logger.exception(
            "Could not delete entities: identity=%s",
            ", ".join(str(identity) for identity in identities),
        )
        raise WriteError(
            "Could not delete entit"
            "{suffix} with identit{suffix}: {identities}".format(
                suffix="y" if len(identities) == 1 else "ies",
                identities=", ".join(str(identity) for identity in identities),
            )
        ) from err

    if len(identities) == 1:
        return identities.pop()

    return sorted(identities)
