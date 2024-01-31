"""Test edge cases for global settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner


CLI_RESULT_FAIL_MESSAGE = "STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"


def test_version(cli: CliRunner) -> None:
    """Test that the version is printed."""
    from entities_service import __version__
    from entities_service.cli.main import APP

    result = cli.invoke(APP, "--version")
    assert result.exit_code == 0, CLI_RESULT_FAIL_MESSAGE.format(
        stdout=result.stdout, stderr=result.stderr
    )
    assert f"entities-service version: {__version__}" in result.stdout.replace(
        "\n", " "
    ), CLI_RESULT_FAIL_MESSAGE.format(stdout=result.stdout, stderr=result.stderr)


def test_dotenv_path(
    cli: CliRunner, tmp_path: Path, pytestconfig: pytest.Config
) -> None:
    """Test that the dotenv path can be set.

    Note, calling 'upload', since it returns the `--help` response on no arguments.
    """
    from entities_service.cli._utils.global_settings import CONTEXT
    from entities_service.cli.main import APP
    from entities_service.service.config import CONFIG

    # Check default value
    default_dotenv_path_value = (
        pytestconfig.invocation_params.dir / str(CONFIG.model_config["env_file"])
    ).resolve()

    assert CONTEXT["dotenv_path"] != tmp_path / ".env"
    assert CONTEXT["dotenv_path"] == default_dotenv_path_value

    # Check that the dotenv path can be set
    dotenv_path = tmp_path / ".env"

    result = cli.invoke(APP, f"--dotenv-config={dotenv_path} upload")
    assert result.exit_code == 0, CLI_RESULT_FAIL_MESSAGE.format(
        stdout=result.stdout, stderr=result.stderr
    )
    assert not result.stderr

    assert CONTEXT["dotenv_path"] == dotenv_path
