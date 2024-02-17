"""Entities endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from pydantic.networks import AnyHttpUrl

from entities_service.models import VersionedSOFTEntity, get_uri
from entities_service.service.backend import get_backend
from entities_service.service.config import CONFIG
from entities_service.service.security import verify_token

LOGGER = logging.getLogger(__name__)

ROUTER = APIRouter(
    prefix="/entities",
    tags=["Entities"],
    responses={404: {"description": "Entites not found"}},
)


@ROUTER.get(
    "/",
    response_model=list[VersionedSOFTEntity],
    response_model_by_alias=True,
    response_model_exclude_unset=True,
)
async def get_entities(
    identities: Annotated[
        list[AnyHttpUrl] | None,
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
) -> list[dict[str, Any]]:
    """Retrieve one or more Entities."""
    backend = get_backend()

    entities = list(
        backend.search(
            by_identity=identities, by_properties=properties, by_dimensions=dimensions
        )
    )

    if entities:
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
    response_model=list[VersionedSOFTEntity] | VersionedSOFTEntity | None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_token)],
)
async def create_entities(
    entities: list[VersionedSOFTEntity] | VersionedSOFTEntity,
    response: Response,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Create one or more Entities."""
    if isinstance(entities, list):
        # Check if there are any entities to create
        if not entities:
            response.status_code = status.HTTP_204_NO_CONTENT
            return None
    else:
        entities = [entities]

    write_fail_exception = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Could not create entit{suffix_entit} with uri{suffix_uri}: {uris}".format(
                suffix_entit="y" if len(entities) == 1 else "ies",
                suffix_uri="" if len(entities) == 1 else "s",
                uris=", ".join(get_uri(entity) for entity in entities),
            )
        ),
    )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    try:
        created_entities = entities_backend.create(entities)
    except entities_backend.write_access_exception as err:
        LOGGER.error(
            "Could not create entities: uris=%s",
            ", ".join(get_uri(entity) for entity in entities),
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
    response_model=list[VersionedSOFTEntity] | VersionedSOFTEntity | None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_token)],
)
async def update_entities(
    entities: list[VersionedSOFTEntity] | VersionedSOFTEntity,
    response: Response,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Replace and/or create one or more Entities."""
    if isinstance(entities, list):
        # Check if there are any entities to update
        if not entities:
            return None
    else:
        entities = [entities]

    write_fail_exception = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Could not put/update entit"
            "{suffix_entit} with uri{suffix_uri}: {uris}".format(
                suffix_entit="y" if len(entities) == 1 else "ies",
                suffix_uri="" if len(entities) == 1 else "s",
                uris=", ".join(get_uri(entity) for entity in entities),
            )
        ),
    )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    new_entities = [
        entity for entity in entities if get_uri(entity) not in entities_backend
    ]

    if new_entities:
        response.status_code = status.HTTP_201_CREATED
        try:
            created_entities = entities_backend.create(new_entities)
        except entities_backend.write_access as err:
            LOGGER.error(
                "Could not create entities: uris=%s",
                ", ".join(get_uri(entity) for entity in new_entities),
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

        if get_uri(entity) in entities_backend:
            try:
                entities_backend.update(get_uri(entity), entity)
            except entities_backend.write_access_exception as err:
                LOGGER.error(
                    "Could not update entities: uris=%s",
                    ", ".join(get_uri(entity) for entity in entities),
                )
                LOGGER.exception(err)
                raise write_fail_exception from err

    if new_entities:
        return created_entities

    return None


@ROUTER.patch(
    "/",
    response_model=None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_token)],
)
async def patch_entities(
    entities: list[dict[str, Any]] | dict[str, Any],
) -> None:
    """Update one or more Entities."""
    if isinstance(entities, list):
        # Check if there are any entities to update
        if not entities:
            return
    else:
        entities = [entities]

    write_fail_exception = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            "Could not patch/update entit"
            "{suffix_entit} with uri{suffix_uri}: {uris}".format(
                suffix_entit="y" if len(entities) == 1 else "ies",
                suffix_uri="" if len(entities) == 1 else "s",
                uris=", ".join(get_uri(entity) for entity in entities),
            )
        ),
    )

    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    # First, check all entities already exist
    non_existing_entities = [
        entity for entity in entities if get_uri(entity) not in entities_backend
    ]
    if non_existing_entities:
        LOGGER.error(
            "Cannot patch non-existant entities: uris=%s",
            ", ".join(get_uri(entity) for entity in non_existing_entities),
        )
        raise write_fail_exception

    for entity in entities:
        try:
            entities_backend.update(get_uri(entity), entity)
        except entities_backend.write_access_exception as err:
            LOGGER.error(
                "Could not update entities: uris=%s",
                ", ".join(get_uri(entity) for entity in entities),
            )
            LOGGER.exception(err)
            raise write_fail_exception from err

    return


@ROUTER.delete(
    "/",
    response_model=list[AnyHttpUrl] | None,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_token)],
)
async def delete_entities(
    identities_body: Annotated[
        list[AnyHttpUrl] | AnyHttpUrl | None,
        Body(
            title="Entity identity",
            description="The identity/-ies (URI/IRI) of the entity/-ies to delete.",
        ),
    ] = None,
    identities_query: Annotated[
        list[AnyHttpUrl] | None,
        Query(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to delete.",
            min_length=1,
            alias="id",
        ),
    ] = None,
) -> list[AnyHttpUrl]:
    """Delete one or more Entities."""
    identities: set[AnyHttpUrl] = set()

    if isinstance(identities_body, AnyHttpUrl):
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
            "Could not delete entities: uri=%s",
            ", ".join(str(identity) for identity in identities),
        )
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Could not delete entit"
                "{suffix_entit} with uri{suffix_uri}: {uris}".format(
                    suffix_entit="y" if len(identities) == 1 else "ies",
                    suffix_uri="" if len(identities) == 1 else "s",
                    uris=", ".join(str(identity) for identity in identities),
                )
            ),
        ) from err

    return identities


@ROUTER.get(
    "/{identity}",
    response_model=VersionedSOFTEntity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
)
async def get_entity(
    identity: Annotated[
        AnyHttpUrl,
        Path(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to retrieve.",
        ),
    ],
) -> dict[str, Any]:
    """Get an entity."""
    entity = get_backend().read(identity)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find entity: uri={identity}",
        )
    return entity


@ROUTER.post(
    "/{identity}",
    response_model=VersionedSOFTEntity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_token)],
)
async def create_entity(
    identity: Annotated[
        AnyHttpUrl,
        Path(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to create.",
        ),
    ],
    entity: VersionedSOFTEntity,
) -> dict[str, Any]:
    """Create an entity."""
    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    try:
        created_entity = entities_backend.create([entity])
    except entities_backend.write_access_exception as err:
        LOGGER.error("Could not create entity: uri=%s", identity)
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not create entity: uri={identity}",
        ) from err

    return created_entity


@ROUTER.put(
    "/{identity}",
    response_model=VersionedSOFTEntity,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_token)],
)
async def update_entity(
    identity: Annotated[
        AnyHttpUrl,
        Path(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to update.",
        ),
    ],
    entity: VersionedSOFTEntity,
    response: Response,
) -> dict[str, Any] | None:
    """Update or create an entity."""
    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    if identity != get_uri(entity):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entity identity mismatch: uri={identity} != {get_uri(entity)}",
        )

    # Create new entity
    if str(identity) not in entities_backend:
        response.status_code = status.HTTP_201_CREATED
        try:
            entities_backend.create([entity])
        except entities_backend.write_access_exception as err:
            LOGGER.error("Could not create entity: uri=%s", identity)
            LOGGER.exception(err)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not create entity: uri={identity}",
            ) from err

        return entity

    # Update existing entity
    try:
        entities_backend.update(identity, entity)
    except entities_backend.write_access_exception as err:
        LOGGER.error("Could not update entity: uri=%s", identity)
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not update entity: uri={identity}",
        ) from err

    return None


@ROUTER.patch(
    "/{identity}",
    response_model=None,
    response_model_by_alias=True,
    response_model_exclude_unset=True,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_token)],
)
async def patch_entity(
    identity: Annotated[
        AnyHttpUrl,
        Path(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to update.",
        ),
    ],
    entity: dict[str, Any],
) -> None:
    """Update an entity."""
    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    if (
        "uri" in entity
        and entity["uri"] != identity
        or (
            "namespace" in entity
            and (
                uri := (
                    f"{entity['namespace'].rstrip('/')}"
                    f"/{entity.get('version')}/{entity.get('name')}"
                )
            )
            != identity
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Entity identity mismatch: uri={identity} != {entity.get('uri', uri)}"
            ),
        )

    if str(identity) not in entities_backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find entity to update: uri={identity}",
        )

    try:
        entities_backend.update(identity, entity)
    except entities_backend.write_access_exception as err:
        LOGGER.error("Could not update entity: uri=%s", identity)
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not update entity: uri={identity}",
        ) from err

    return


@ROUTER.delete(
    "/{identity}",
    response_model=AnyHttpUrl,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_token)],
)
async def delete_entity(
    identity: Annotated[
        AnyHttpUrl,
        Path(
            title="Entity identity",
            description="The identity (URI/IRI) of the entity to delete.",
        ),
    ],
) -> AnyHttpUrl:
    """Delete an entity."""
    entities_backend = get_backend(CONFIG.backend, auth_level="write")

    if str(identity) not in entities_backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find entity to delete: uri={identity}",
        )

    try:
        entities_backend.delete([identity])
    except entities_backend.write_access_exception as err:
        LOGGER.error("Could not delete entity: uri=%s", identity)
        LOGGER.exception(err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not delete entity: uri={identity}",
        ) from err

    return identity
