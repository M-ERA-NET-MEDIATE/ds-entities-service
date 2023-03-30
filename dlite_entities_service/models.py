"""Pydantic models."""
from typing import Literal

from pydantic import BaseModel, Field, validator
from pydantic.networks import AnyHttpUrl

from dlite_entities_service.config import CONFIG


class DLiteProperty(BaseModel):
    """The defining metadata for a DLite Entity's property."""

    name: str | None = Field(
        None,
        description=(
            "The name of the property. This is not necessary if the SOFT7 approach to "
            "entities are taken."
        ),
    )
    type_: str = Field(
        ...,
        alias="type",
        description="The type of the described property, e.g., an integer.",
    )
    ref: AnyHttpUrl | None = Field(
        None,
        alias="$ref",
        definition=(
            "Formally a part of type. `$ref` is used together with the `ref` type, "
            "which is a special datatype for referring to other instances."
        ),
    )
    shape: list[str] | None = Field(
        None,
        description=(
            "The dimension of multi-dimensional properties. This is a list of "
            "dimension expressions referring to the dimensions defined above. For "
            "instance, if an entity have dimensions with names `H`, `K`, and `L` and "
            "a property with shape `['K', 'H+1']`, the property of an instance of "
            "this entity with dimension values `H=2`, `K=2`, `L=6` will have shape "
            "`[2, 3]`."
        ),
    )
    unit: str | None = Field(None, description="The unit of the property.")
    description: str = Field(
        ..., description="A human-readable description of the property."
    )


class Entity(BaseModel):
    """A DLite Entity returned from this service."""

    uri: AnyHttpUrl = Field(
        ...,
        description=(
            "The universal identifier for the entity. This MUST start with the base "
            "URL."
        ),
    )
    meta: Literal["http://onto-ns.com/meta/0.3/EntitySchema"] = Field(
        ...,
        description=(
            "URI for the metadata entity. For all entities at onto-ns.com, the "
            "EntitySchema v0.3 is used."
        ),
    )
    description: str = Field("", description="Description of the entity.")
    dimensions: dict[str, str] = Field(
        {}, description="A dict of dimensions with an accompanying description."
    )
    properties: dict[str, DLiteProperty] = Field(
        ...,
        description=(
            "A dictionary of properties, mapping the property name to a dictionary of "
            "metadata defining the property."
        ),
    )

    @validator("uri")
    def _validate_base_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        """Validate `uri` starts with the current base URL for the service."""
        if not value.startswith(CONFIG.base_url):
            raise ValueError(
                f"This service only works with DLite entities at {CONFIG.base_url}."
            )
        return value
