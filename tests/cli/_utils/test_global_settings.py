"""Test edge cases for global settings."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typer.testing import CliRunner


def test_version(cli: CliRunner) -> None:
    """Test that the version is printed."""
    from dlite_entities_service import __version__
    from dlite_entities_service.cli.main import APP

    result = cli.invoke(APP, "--version")
    assert result.exit_code == 0, result.stderr
    assert f"dlite-entities-service version: {__version__}" in result.stdout.replace(
        "\n", " "
    ), result.stdout
