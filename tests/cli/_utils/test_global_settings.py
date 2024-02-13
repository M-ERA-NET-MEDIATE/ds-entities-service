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


def test_cache_dir_creation(cli: CliRunner, tmp_cache_dir: Path) -> None:
    """Ensure the cache directiory is created if it does not already exist.

    Note, the callback to `global_settings` is not done if invoking the CLI without any
    arguments. It will instead go straight to outputting the help.
    However, when calling any command, `global_settings` is called.
    Hence, `upload` is called here, which will simply return the help for that command.
    """
    from entities_service.cli.main import APP

    # tmp_cache_dir should not yet exist
    assert not tmp_cache_dir.exists()

    result = cli.invoke(APP, "upload")
    assert result.exit_code == 0, CLI_RESULT_FAIL_MESSAGE.format(
        stdout=result.stdout, stderr=result.stderr
    )
    assert not result.stderr

    # tmp_cache_dir should now exist
    assert tmp_cache_dir.exists()


def test_cache_dir_permissionerror(cli: CliRunner, tmp_path: Path) -> None:
    """Ensure a PermissionError is raised and handled if the cache dir cannot be
    created.

    Note, the callback to `global_settings` is not done if invoking the CLI without any
    arguments. It will instead go straight to outputting the help.
    However, when calling any command, `global_settings` is called.
    Hence, `upload` is called here, which will simply return the help for that command.
    """
    from entities_service.cli.main import APP

    org_mode = tmp_path.stat().st_mode
    tmp_path.chmod(0x555)

    result = cli.invoke(APP, "upload")
    assert result.exit_code != 0, CLI_RESULT_FAIL_MESSAGE.format(
        stdout=result.stdout, stderr=result.stderr
    )
    assert not result.stdout

    assert "Error: " in result.stderr
    assert "is not writable. Please check your permissions." in result.stderr

    tmp_path.chmod(org_mode)
