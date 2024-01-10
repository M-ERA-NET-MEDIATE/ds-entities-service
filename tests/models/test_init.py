"""Test functions for models/__init__.py"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


def test_soft_entity(static_dir: Path) -> None:
    """Test soft_entity function."""
    import json

    from dlite_entities_service.models import soft_entity
    from dlite_entities_service.models.soft5 import SOFT5Entity
    from dlite_entities_service.models.soft7 import SOFT7Entity

    # Test that the function returns the correct version of the entity
    soft5_model_file = static_dir / "valid_entities" / "Cat.json"
    soft7_model_file = static_dir / "valid_entities" / "Dog.json"

    soft5_model = json.loads(soft5_model_file.read_text())
    soft7_model = json.loads(soft7_model_file.read_text())

    assert soft_entity(**soft5_model) == SOFT5Entity(**soft5_model)
    assert soft_entity(**soft7_model) == SOFT7Entity(**soft7_model)


def test_soft_entity_error(static_dir: Path) -> None:
    """Test soft_entity function errors as expected."""
    import json

    from pydantic import ValidationError

    from dlite_entities_service.models import soft_entity
    from dlite_entities_service.models.soft5 import SOFT5Entity
    from dlite_entities_service.models.soft7 import SOFT7Entity

    # Test that the function returns the correct version of the entity
    invalid_model_file = static_dir / "invalid_entities" / "Cat.json"
    invalid_model = json.loads(invalid_model_file.read_text())

    with pytest.raises(ValueError, match=r"^Cannot instantiate entity\. Errors:.*"):
        soft_entity(**invalid_model)

    errors = soft_entity(return_errors=True, **invalid_model)

    expected_errors = []
    try:
        SOFT7Entity(**invalid_model)
    except ValidationError as exc:
        expected_errors.append(exc)

    try:
        SOFT5Entity(**invalid_model)
    except ValidationError as exc:
        expected_errors.append(exc)

    assert [str(_) for _ in errors] == [str(_) for _ in expected_errors]


def test_get_uri(static_dir: Path) -> None:
    """Test get_uri function."""
    import json

    from dlite_entities_service.models import get_uri, soft_entity

    # Test that the function returns the correct version of the entity
    model_file = static_dir / "valid_entities" / "Cat.json"
    model = json.loads(model_file.read_text())

    expected_uri = model["uri"]
    assert expected_uri, model

    # We are currently only interested in the case where the uri is set
    assert all(model.get(_) is None for _ in ("name", "version", "namespace"))

    entity = soft_entity(**model)

    assert str(entity.uri) == expected_uri

    assert get_uri(entity) == str(entity.uri) == expected_uri

    # Reset uri from the model and add namespace, name, and version instead
    entity.uri = None
    entity.namespace = "http://onto-ns.com/meta"
    entity.version = "0.1"
    entity.name = "Cat"

    assert (
        get_uri(entity)
        == f"{entity.namespace}/{entity.version}/{entity.name}"
        == expected_uri
    )


def test_get_version(static_dir: Path) -> None:
    """Test get_version function."""
    import json

    from dlite_entities_service.models import URI_REGEX, get_version, soft_entity

    # Test that the function returns the correct version of the entity based on the URI
    model_file = static_dir / "valid_entities" / "Cat.json"
    model: dict[str, Any] = json.loads(model_file.read_text())

    split_uri = URI_REGEX.match(model["uri"]).groupdict()
    expected_version = split_uri["version"]

    entity = soft_entity(**model)

    assert entity.version is None

    assert get_version(entity) == expected_version

    # Reset uri from the model and add namespace, name, and version instead
    model.update(split_uri)
    model.pop("uri")

    entity = soft_entity(**model)

    assert entity.uri is None

    assert get_version(entity) == entity.version == expected_version

    # Check a ValueError is raised if the version cannot be found
    entity.uri = "http://onto-ns.com/meta/v0.1/Cat"
    entity.version = None

    with pytest.raises(ValueError, match=r"^Cannot parse URI to get version\.$"):
        get_version(entity)


@pytest.mark.parametrize(
    ("version", "expected_updated_version"),
    [
        ("1", "1.1"),
        ("1.1", "1.1.1"),
        ("1.1.1", "1.1.2"),
        ("1.0", "1.0.1"),
        ("1.0.0", "1.0.1"),
    ],
)
def test_get_updated_version(
    static_dir: Path, version: str, expected_updated_version: str
) -> None:
    """Test get_updated_version function.

    Current logic:
    If version is just MAJOR, add and increment MINOR by 1
    If version is MAJOR.MINOR, add and increment PATCH by 1
    If version is MAJOR.MINOR.PATCH, increment PATCH by 1
    """
    import json

    from dlite_entities_service.models import get_updated_version, soft_entity

    model_file = static_dir / "valid_entities" / "Cat.json"
    model: dict[str, Any] = json.loads(model_file.read_text())

    entity = soft_entity(**model)
    entity.uri = None

    entity.version = version
    assert get_updated_version(entity) == expected_updated_version


def test_get_updated_version_errors(static_dir: Path) -> None:
    """Test get_updated_version function errors as expected."""
    import json

    from dlite_entities_service.models import get_updated_version, soft_entity

    model_file = static_dir / "valid_entities" / "Cat.json"
    model: dict[str, Any] = json.loads(model_file.read_text())

    entity = soft_entity(**model)
    entity.uri = None

    # Check a ValueError is raised if the version is not a numeric string
    entity.version = "one"
    with pytest.raises(
        ValueError, match=r"^Cannot parse version to get updated version.*"
    ):
        get_updated_version(entity)

    # Check a ValueError is raised if the version is not a simple MAJOR.MINOR.PATCH
    # styling
    entity.version = "1.2.3.4"
    with pytest.raises(
        ValueError, match=r"^Cannot parse version to get updated version.*"
    ):
        get_updated_version(entity)
