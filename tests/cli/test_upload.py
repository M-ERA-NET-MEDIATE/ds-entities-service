"""Tests for `entities-service upload` CLI command."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from pymongo.collection import Collection
    from typer.testing import CliRunner


def test_upload_no_args(cli: CliRunner) -> None:
    """Test `entities-service upload` CLI command."""
    from dlite_entities_service.cli.main import APP, upload

    result = cli.invoke(APP, "upload")
    assert result.exit_code == 0, result.stderr
    assert upload.__doc__ in result.stdout

    assert result.stdout == cli.invoke(APP, "upload --help").stdout


def test_upload_filepath(
    cli: CliRunner, static_dir: Path, mock_entities_collection: Collection
) -> None:
    """Test upload with a filepath."""
    import json

    from dlite_entities_service.cli import main

    result = cli.invoke(
        main.APP, f"upload --file {static_dir / 'valid_entities' / 'Person.json'}"
    )
    assert result.exit_code == 0, result.stderr

    assert mock_entities_collection.count_documents({}) == 1
    stored_entity: dict[str, Any] = mock_entities_collection.find_one({})
    stored_entity.pop("_id")
    assert stored_entity == json.loads(
        (static_dir / "valid_entities" / "Person.json").read_bytes()
    )

    assert "Successfully uploaded 1 entity:" in result.stdout


@pytest.mark.parametrize("fail_fast", [True, False])
def test_upload_filepath_invalid(
    cli: CliRunner, static_dir: Path, fail_fast: bool
) -> None:
    """Test upload with an invalid filepath."""
    from dlite_entities_service.cli.main import APP

    result = cli.invoke(
        APP,
        f"upload {'--fail-fast ' if fail_fast else ''}"
        f"--file {static_dir / 'invalid_entities' / 'Person.json'}",
    )
    assert result.exit_code == 1, result.stdout
    assert "Person.json is not a valid SOFT entity:" in result.stderr.replace("\n", "")
    assert "validation error for SOFT7Entity" in result.stderr.replace("\n", "")
    assert "validation errors for SOFT5Entity" in result.stderr.replace("\n", "")
    assert not result.stdout
    if fail_fast:
        assert (
            "Failed to upload 1 entity, see above for more details:"
            not in result.stderr.replace("\n", "")
        )
    else:
        assert (
            "Failed to upload 1 entity, see above for more details:"
            in result.stderr.replace("\n", "")
        )


def test_upload_filepath_invalid_format(cli: CliRunner, tmp_path: Path) -> None:
    """Test upload with an invalid file format."""
    from dlite_entities_service.cli.main import APP

    (tmp_path / "Person.txt").touch()

    result = cli.invoke(APP, f"upload --file {tmp_path / 'Person.txt'}")
    assert result.exit_code == 0, result.stderr
    assert result.stderr.count("File format 'txt' is not supported.") == 1
    assert "No entities were uploaded." in result.stdout


def test_upload_no_file_or_dir(cli: CliRunner) -> None:
    """Test error when no file or directory is provided."""
    from dlite_entities_service.cli.main import APP

    result = cli.invoke(APP, "upload --format json")
    assert result.exit_code == 1, result.stdout
    assert "Missing either option '--file' / '-f'" in result.stderr
    assert not result.stdout


def test_upload_directory(
    cli: CliRunner, static_dir: Path, mock_entities_collection: Collection
) -> None:
    """Test upload with a directory."""
    import json

    from dlite_entities_service.cli import main

    directory = static_dir / "valid_entities"

    result = cli.invoke(main.APP, f"upload --dir {directory}")
    assert result.exit_code == 0, result.stderr

    original_entities = list(directory.glob("*.json"))

    assert mock_entities_collection.count_documents({}) == len(original_entities)

    stored_entities = list(mock_entities_collection.find({}))
    for stored_entity in stored_entities:
        # Remove MongoDB ID
        stored_entity.pop("_id")

    for sample_file in original_entities:
        # If the sample file contains a '$ref' key, it will be stored in the DB as 'ref'
        # instead. This is due to the fact that MongoDB does not allow keys to start
        # with a '$' character.
        parsed_sample_file: dict[str, Any] = json.loads(sample_file.read_bytes())
        if isinstance(parsed_sample_file["properties"], list):
            for index, property_value in enumerate(
                list(parsed_sample_file["properties"])
            ):
                if "$ref" in property_value:
                    property_value["ref"] = property_value.pop("$ref")
                    parsed_sample_file["properties"][index] = property_value
        else:
            # Expect "properties" to be a dict
            for property_name, property_value in list(
                parsed_sample_file["properties"].items()
            ):
                if "$ref" in property_value:
                    property_value["ref"] = property_value.pop("$ref")
                    parsed_sample_file["properties"][property_name] = property_value

        assert parsed_sample_file in stored_entities

    assert f"Successfully uploaded {len(original_entities)} entities:" in result.stdout


def test_upload_empty_dir(cli: CliRunner, tmp_path: Path) -> None:
    """Test upload with no valid files found.

    The outcome here should be the same whether an empty directory is
    provided or a directory with only invalid files.
    """
    from dlite_entities_service.cli import main

    empty_dir = tmp_path / "empty_dir"
    assert not empty_dir.exists()
    empty_dir.mkdir()

    yaml_dir = tmp_path / "yaml_dir"
    assert not yaml_dir.exists()
    yaml_dir.mkdir()
    (yaml_dir / "Person.yaml").touch()

    for directory in (empty_dir, yaml_dir):
        result = cli.invoke(main.APP, f"upload --format json --dir {directory}")
        assert result.exit_code == 1, result.stderr
        assert "Error: No files found with the given options." in result.stderr.replace(
            "│\n│ ", ""
        ), result.stderr
        assert not result.stdout


def test_upload_files_with_unchosen_format(cli: CliRunner, static_dir: Path) -> None:
    """Test upload several files with a format not chosen."""
    from dlite_entities_service.cli.main import APP

    directory = static_dir / "valid_entities"
    file_inputs = " ".join(
        f"--file={filepath}" for filepath in directory.glob("*.json")
    )

    result = cli.invoke(APP, f"upload --format yaml {file_inputs}")
    assert result.exit_code == 0, result.stderr
    assert "No entities were uploaded." in result.stdout
    assert all(
        f"Skipping file: {filepath}" in result.stdout.replace("\n", "")
        for filepath in directory.glob("*.json")
    )
    assert (
        result.stdout.replace("\n", "").count(
            "Entities using the file format 'json' can be uploaded by adding the "
            "option: --format=json"
        )
        == 1
    )
    assert not result.stderr


@pytest.mark.parametrize("fail_fast", [True, False])
def test_upload_directory_invalid_entities(
    cli: CliRunner, static_dir: Path, fail_fast: bool
) -> None:
    """Test uploading a directory full of invalid entities."""
    import re

    from dlite_entities_service.cli.main import APP

    directory = static_dir / "invalid_entities"

    result = cli.invoke(
        APP, f"upload {'--fail-fast ' if fail_fast else ''}--dir {directory}"
    )
    assert result.exit_code == 1, result.stderr
    assert (
        re.search(
            r"validation errors? for SOFT7Entity", result.stderr.replace("\n", "")
        )
        is not None
    )
    assert (
        re.search(
            r"validation errors? for SOFT5Entity", result.stderr.replace("\n", "")
        )
        is not None
    )
    assert not result.stdout

    if fail_fast:
        errored_entity = set()
        for invalid_entity in directory.glob("*.json"):
            if (
                f"{invalid_entity.name} is not a valid SOFT entity:"
                in result.stderr.replace("\n", "")
            ):
                errored_entity.add(invalid_entity.name)
        assert len(errored_entity) == 1

        assert (
            f"Failed to upload {len(list(directory.glob('*.json')))} entities, see "
            "above for more details:" not in result.stderr.replace("\n", "")
        )
    else:
        assert all(
            f"{invalid_entity.name} is not a valid SOFT entity:"
            in result.stderr.replace("\n", "")
            for invalid_entity in directory.glob("*.json")
        )

        assert (
            f"Failed to upload {len(list(directory.glob('*.json')))} entities, see "
            "above for more details:" in result.stderr.replace("\n", "")
        )


def test_get_backend(
    cli: CliRunner,
    dotenv_file: Path,
    static_dir: Path,
    mock_entities_collection: Collection,
) -> None:
    """Test that a found '.env' file is utilized."""
    import json

    from dotenv import set_key

    from dlite_entities_service.cli._utils.global_settings import CONTEXT
    from dlite_entities_service.cli.main import APP

    # Create a temporary '.env' file
    if not dotenv_file.exists():
        dotenv_file.touch()
    else:
        dotenv_file.unlink()
        dotenv_file.touch()
    set_key(dotenv_file, "ENTITY_SERVICE_MONGO_URI", "mongodb://localhost:27017")

    CONTEXT["dotenv_path"] = dotenv_file

    result = cli.invoke(
        APP, f"upload --file {static_dir / 'valid_entities' / 'Person.json'}"
    )
    assert result.exit_code == 0, result.stderr

    assert mock_entities_collection.count_documents({}) == 1
    stored_entity: dict[str, Any] = mock_entities_collection.find_one({})
    stored_entity.pop("_id")
    assert stored_entity == json.loads(
        (static_dir / "valid_entities" / "Person.json").read_bytes()
    )

    assert "Successfully uploaded 1 entity:" in result.stdout, result.stdout


def test_existing_entity(
    cli: CliRunner, static_dir: Path, mock_entities_collection: Collection
) -> None:
    """Test that an existing entity is not overwritten."""
    from dlite_entities_service.cli.main import APP

    result = cli.invoke(
        APP, f"upload --file {static_dir / 'valid_entities' / 'Person.json'}"
    )
    assert result.exit_code == 0, result.stderr

    result = cli.invoke(
        APP, f"upload --file {static_dir / 'valid_entities' / 'Person.json'}"
    )
    assert result.exit_code == 0, result.stderr
    assert "Entity already exists in the database." in result.stdout.replace(
        "\n", ""
    ), result.stderr
    assert "No entities were uploaded." in result.stdout.replace(
        "\n", ""
    ), result.stderr
    assert not result.stderr

    assert mock_entities_collection.count_documents({}) == 1


def test_existing_entity_different_content(
    cli: CliRunner,
    static_dir: Path,
    mock_entities_collection: Collection,
    tmp_path: Path,
) -> None:
    """Test that an incoming entity can be uploaded with a new version due to an
    existance collision."""
    import json
    from copy import deepcopy

    from dlite_entities_service.cli.main import APP
    from dlite_entities_service.service.config import CONFIG

    raw_entity = (static_dir / "valid_entities" / "Person.json").read_text()
    parsed_entity: dict[str, Any] = json.loads(raw_entity)

    result = cli.invoke(
        APP, f"upload --file {static_dir / 'valid_entities' / 'Person.json'}"
    )
    assert (
        result.exit_code == 0
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    assert mock_entities_collection.count_documents({}) == 1
    db_entity = mock_entities_collection.find_one({})
    for key in db_entity:
        if key == "_id":
            continue
        assert key in parsed_entity
        assert db_entity[key] == parsed_entity[key]

    # Create a new file with a change in the content
    new_entity = deepcopy(parsed_entity)
    new_entity["dimensions"]["n_skills"] = "Skill number."
    new_entity["namespace"] = str(CONFIG.base_url)
    new_entity["version"] = "0.1"
    new_entity["name"] = "Person"
    assert new_entity != parsed_entity
    new_entity_file = tmp_path / "Person.json"
    new_entity_file.write_text(json.dumps(new_entity))

    # First, let's check we skip the file if not wanting to update the version
    result = cli.invoke(
        APP,
        f"upload --file {tmp_path / 'Person.json'}",
        input="n\n",
    )
    assert (
        result.exit_code == 0
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert (
        "Entity already exists in the database, but they differ in their content."
        in result.stdout.replace("\n", "")
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Skipping file:" in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "No entities were uploaded." in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert not result.stderr

    # Now, let's check we update the version if wanting to.
    # Use default generated version. An existing version of '0.1' should generate
    # '0.1.1'.
    result = cli.invoke(
        APP,
        f"upload --file {tmp_path / 'Person.json'}",
        input="y\n\n",
    )
    assert (
        result.exit_code == 0
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert (
        "Entity already exists in the database, but they differ in their content."
        in result.stdout.replace("\n", "")
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Skipping file:" not in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Successfully uploaded 1 entity:" in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert not result.stderr

    assert mock_entities_collection.count_documents({}) == 2
    assert (
        mock_entities_collection.find_one({"uri": f"{CONFIG.base_url}/0.1.1/Person"})
        is not None
    )

    db_entities = list(mock_entities_collection.find({}))
    assert len(db_entities) == 2
    assert db_entity in db_entities
    new_db_entity = next(_ for _ in db_entities if _ != db_entity)
    for key in new_db_entity:
        if key == "_id":
            continue
        if key == "uri":
            assert new_db_entity[key] == f"{CONFIG.base_url}/0.1.1/Person"
            continue
        if key == "version":
            assert new_db_entity[key] == "0.1.1"
            continue
        assert key in new_entity
        assert new_db_entity[key] == new_entity[key]

    # Now, let's check we update the version if wanting to.
    # Use custom version.
    result = cli.invoke(
        APP,
        f"upload --file {tmp_path / 'Person.json'}",
        input="y\n0.2\n",
    )
    assert (
        result.exit_code == 0
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert (
        "Entity already exists in the database, but they differ in their content."
        in result.stdout.replace("\n", "")
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Skipping file:" not in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Successfully uploaded 1 entity:" in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert not result.stderr

    assert mock_entities_collection.count_documents({}) == 3
    assert (
        mock_entities_collection.find_one({"uri": f"{CONFIG.base_url}/0.2/Person"})
        is not None
    )


@pytest.mark.parametrize("fail_fast", [True, False])
def test_existing_entity_errors(
    cli: CliRunner,
    static_dir: Path,
    mock_entities_collection: Collection,
    tmp_path: Path,
    fail_fast: bool,
) -> None:
    """Test that an incoming entity with existing URI is correctly aborted in certain
    cases."""
    import json
    from copy import deepcopy

    from dlite_entities_service.cli.main import APP

    raw_entity = (static_dir / "valid_entities" / "Person.json").read_text()
    parsed_entity: dict[str, Any] = json.loads(raw_entity)

    result = cli.invoke(
        APP, f"upload --file {static_dir / 'valid_entities' / 'Person.json'}"
    )
    assert (
        result.exit_code == 0
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    assert mock_entities_collection.count_documents({}) == 1
    db_entity = mock_entities_collection.find_one({})
    for key in db_entity:
        if key == "_id":
            continue
        assert key in parsed_entity
        assert db_entity[key] == parsed_entity[key]

    # Create a new file with a change in the content
    new_entity = deepcopy(parsed_entity)
    new_entity["dimensions"]["n_skills"] = "Skill number."
    assert new_entity != parsed_entity
    new_entity_file = tmp_path / "Person.json"
    new_entity_file.write_text(json.dumps(new_entity))

    # Let's check an error occurs if the version change is to the existing version.
    # The existing version is '0.1'.
    result = cli.invoke(
        APP,
        f"upload {'--fail-fast ' if fail_fast else ''}"
        f"--file {tmp_path / 'Person.json'}",
        input="y\n0.1\n",
    )
    assert (
        result.exit_code == 1
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert (
        "Entity already exists in the database, but they differ in their content."
        in result.stdout.replace("\n", "")
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Skipping file:" not in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert (
        "New version (0.1) is the same as the existing version (0.1)."
        in result.stderr.replace("\n", "")
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    if fail_fast:
        assert "Failed to upload 1 entity" not in result.stderr.replace(
            "\n", ""
        ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    else:
        assert "Failed to upload 1 entity" in result.stderr.replace(
            "\n", ""
        ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    # Let's check an error occurs if the version is not of the type MAJOR.MINOR.PATCH.
    result = cli.invoke(
        APP,
        f"upload {'--fail-fast ' if fail_fast else ''}"
        f"--file {tmp_path / 'Person.json'}",
        input="y\nv0.1\n",
    )
    assert (
        result.exit_code == 1
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert (
        "Entity already exists in the database, but they differ in their content."
        in result.stdout.replace("\n", "")
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "Skipping file:" not in result.stdout.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    assert "New version (v0.1) is not a valid SOFT version." in result.stderr.replace(
        "\n", ""
    ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    if fail_fast:
        assert "Failed to upload 1 entity" not in result.stderr.replace(
            "\n", ""
        ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    else:
        assert "Failed to upload 1 entity" in result.stderr.replace(
            "\n", ""
        ), f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
