"""Various routers for the service."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Generator

    from fastapi import APIRouter


def get_routers() -> Generator[APIRouter]:
    """Get the routers."""
    this_dir = Path(__file__).parent.resolve()

    for path in this_dir.glob("*.py"):
        if path.stem == "__init__":
            continue

        module = import_module(f".{path.stem}", __package__)

        if not hasattr(module, "ROUTER"):
            raise RuntimeError(f"Module {module.__name__} has no ROUTER")

        yield module.ROUTER
