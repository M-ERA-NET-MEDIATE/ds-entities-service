"""Customize running application with uvicorn."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from uvicorn.workers import UvicornWorker as OriginalUvicornWorker

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


class UvicornWorker(OriginalUvicornWorker):
    """Uvicorn worker class to be used in production with gunicorn."""

    CONFIG_KWARGS: ClassVar[dict[str, Any]] = {
        "server_header": False,
        "headers": [("Server", "EntitiesService")],
    }
