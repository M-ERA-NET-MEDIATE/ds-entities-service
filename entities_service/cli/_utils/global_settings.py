"""Global settings for the CLI."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

try:
    import typer
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Please install the entities service utility CLI with 'pip install "
        f"{Path(__file__).resolve().parent.parent.parent.parent.resolve()}[cli]'"
    ) from exc

from entities_service import __version__
from entities_service.cli._utils.generics import print
from entities_service.service.config import CONFIG

if TYPE_CHECKING:  # pragma: no cover
    from typing import TypedDict

    class ContextDict(TypedDict):
        """Global context for the CLI."""

        dotenv_path: Path


CONTEXT: ContextDict = {
    "dotenv_path": (Path().cwd() / str(CONFIG.model_config["env_file"])).resolve()
}
"""Global context for the CLI used to communicate global options."""

# Type Aliases
OptionalBool = Optional[bool]
OptionalPath = Optional[Path]


def print_version(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"entities-service version: {__version__}")
        raise typer.Exit()


def global_options(
    _: OptionalBool = typer.Option(
        None,
        "--version",
        help="Show version and exit.",
        is_eager=True,
        callback=print_version,
    ),
    dotenv_path: OptionalPath = typer.Option(
        None,
        "--dotenv-config",
        exists=False,
        dir_okay=False,
        file_okay=True,
        readable=True,
        writable=True,
        resolve_path=True,
        help=(
            "Use the .env file at the given location for the current command. "
            "By default it will point to the .env file in the current directory."
        ),
        show_default=False,
        rich_help_panel="Global options",
    ),
) -> None:
    """Global options for the CLI."""
    if dotenv_path is not None:
        CONTEXT["dotenv_path"] = dotenv_path
