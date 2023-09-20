"""SOFT models."""
from pydantic import ValidationError

from .soft5 import SOFT5Entity
from .soft7 import SOFT7Entity

VersionedSOFTEntity = SOFT5Entity | SOFT7Entity


def soft_entity(*args, **kwargs) -> VersionedSOFTEntity:
    """Return the correct version of the SOFT Entity."""
    errors = []
    for versioned_entity_cls in (SOFT7Entity, SOFT5Entity):
        try:
            new_object = versioned_entity_cls(*args, **kwargs)
            break
        except ValidationError as exc:
            errors.append(exc)
            continue
    else:
        raise ValueError(
            "Cannot instantiate entity. Errors:\n"
            + "\n".join(str(error) for error in errors)
        )
    return new_object  # type: ignore[return-value]
