"""Fixtures for the utils_cli tests."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from pymongo.collection import Collection
    from typer import Typer
    from typer.testing import CliRunner


@pytest.fixture()
def cli() -> CliRunner:
    """Fixture for CLI runner."""
    import os

    from typer.testing import CliRunner

    return CliRunner(mix_stderr=False, env=os.environ.copy())


@pytest.fixture()
def mock_entities_collection(monkeypatch: pytest.MonkeyPatch) -> Collection:
    """Return a mock entities collection."""
    from mongomock import MongoClient

    from dlite_entities_service.service import backend
    from dlite_entities_service.service.config import CONFIG

    mongo_client = MongoClient(str(CONFIG.mongo_uri))
    mock_entities_collection = mongo_client["dlite"]["entities"]

    monkeypatch.setattr(backend, "ENTITIES_COLLECTION", mock_entities_collection)
    monkeypatch.setattr(
        backend,
        "get_collection",
        lambda *args, **kwargs: mock_entities_collection,  # noqa: ARG005
    )

    return mock_entities_collection


@pytest.fixture(scope="session")
def config_app() -> Typer:
    """Return the config APP."""
    from dlite_entities_service.cli._utils.global_settings import global_options
    from dlite_entities_service.cli.config import APP

    # Add global options to the APP
    # This is done by the "main" APP, and should hence be done here manually to ensure
    # they can be used
    APP.callback()(global_options)

    return APP


@pytest.fixture()
def dotenv_file(tmp_path: Path) -> Path:
    """Create a path to a dotenv file in a temporary test folder."""
    from dlite_entities_service.service.config import CONFIG

    env_file = CONFIG.model_config["env_file"]

    assert isinstance(env_file, str)

    return tmp_path / env_file


@pytest.fixture()
def _prefill_dotenv_config(dotenv_file: Path) -> None:
    """'Pre'-fill the monkeypatched dotenv config paths."""
    from dotenv import set_key

    from dlite_entities_service.cli.config import ConfigFields
    from dlite_entities_service.service.config import CONFIG

    env_prefix = CONFIG.model_config["env_prefix"]

    if not dotenv_file.exists():
        dotenv_file.touch()

    for field in ConfigFields:
        set_key(dotenv_file, f"{env_prefix}{field}".upper(), f"{field}_test")
