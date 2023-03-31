"""Customize running application with uvicorn."""
from uvicorn.workers import UvicornWorker as OriginalUvicornWorker


class UvicornWorker(OriginalUvicornWorker):
    """Uvicorn worker class to be used in production with gunicorn."""

    CONFIG_KWARGS = {
        "server_header": False,
        "headers": [("Server", "DLiteEntitiesService")],
    }
