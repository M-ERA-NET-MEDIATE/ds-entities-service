"""SOFT models."""

from __future__ import annotations

from typing import TYPE_CHECKING, get_args, overload

from pydantic import ValidationError

from .soft5 import URI_REGEX, SOFT5Entity
from .soft7 import SOFT7Entity

if TYPE_CHECKING:  # pragma: no cover
    from typing import Literal

VersionedSOFTEntity = SOFT7Entity | SOFT5Entity
SOFTModelTypes = (SOFT7Entity, SOFT5Entity)


@overload
def soft_entity(
    *, return_errors: Literal[False] = False, error_msg: str | None = None, **fields
) -> VersionedSOFTEntity:  # pragma: no cover
    ...


@overload
def soft_entity(
    *, return_errors: Literal[True], error_msg: str | None = None, **fields
) -> VersionedSOFTEntity | list[ValidationError]:  # pragma: no cover
    ...


def soft_entity(*, return_errors: bool = False, error_msg: str | None = None, **fields):
    """Return the correct version of the SOFT Entity."""
    errors = []
    for versioned_entity_cls in get_args(VersionedSOFTEntity):
        try:
            new_object = versioned_entity_cls(**fields)
            break
        except ValidationError as exc:
            errors.append(exc)
            continue
    else:
        if return_errors:
            return errors

        if error_msg is None:
            error_msg = "Cannot instantiate entity."

        raise ValueError(f"{error_msg}\nErrors:\n" + "\n\n".join(str(error) for error in errors))
    return new_object  # type: ignore[return-value]


def get_uri(entity: VersionedSOFTEntity) -> str:
    """Return the URI of the entity."""
    if entity.uri is not None:
        return str(entity.uri)

    return f"{entity.namespace}/{entity.version}/{entity.name}"


def get_version(entity: VersionedSOFTEntity) -> str:
    """Return the version of the entity."""
    if entity.version is not None:
        return entity.version

    if (match := URI_REGEX.match(str(entity.uri))) is not None:
        return str(match.group("version"))

    raise ValueError("Cannot parse URI to get version.")


def get_updated_version(entity: VersionedSOFTEntity) -> str:
    """Return the updated version of the entity."""
    current_version = get_version(entity)

    error_message = (
        "Cannot parse version to get updated version. Expecting version to be "
        "a simple MAJOR, MAJOR.MINOR, or MAJOR.MINOR.PATCH styling."
    )

    # Do simple logic, expecting version to be either:
    #  - MAJOR
    #  - MAJOR.MINOR
    #  - MAJOR.MINOR.PATCH
    split_version = current_version.split(".")

    # Check we are dealing with integers in split_version
    if not all(version_part.isnumeric() for version_part in split_version):
        raise ValueError(error_message)

    major_length = 1
    minor_length = 2
    patch_length = 3

    # If version is just MAJOR, add and increment MINOR by 1
    # If version is MAJOR.MINOR, add and increment PATCH by 1
    # If version is MAJOR.MINOR.PATCH, increment PATCH by 1

    if len(split_version) == major_length:
        return f"{split_version[0]}.1"

    if len(split_version) == minor_length:
        return f"{split_version[0]}.{split_version[1]}.1"

    if len(split_version) == patch_length:
        return f"{split_version[0]}.{split_version[1]}.{int(split_version[2]) + 1}"

    raise ValueError(error_message)
