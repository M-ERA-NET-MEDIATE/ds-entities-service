"""Logging to file."""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from uvicorn.logging import DefaultFormatter

from dataspaces_entities.config import get_config

if TYPE_CHECKING:  # pragma: no cover
    import logging.handlers


@contextmanager
def disable_logging():
    """Temporarily disable logging.

    Usage:

    ```python
    from dataspaces_entities.logger import disable_logging

    # Do stuff, logging to all handlers.
    # ...
    with disable_logging():
        # Do stuff, without logging to any handlers.
        # ...
    # Do stuff, logging to all handlers now re-enabled.
    # ...
    ```

    """
    try:
        # Disable logging lower than CRITICAL level
        logging.disable(logging.CRITICAL)
        yield
    finally:
        # Re-enable logging to desired levels
        logging.disable(logging.NOTSET)


def _get_service_logger_handlers() -> list[logging.Handler]:
    """Return a list of handlers for the service logger."""
    config = get_config()

    # Create logs directory
    root_dir = Path(__file__).resolve().parent.parent
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Set handlers
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "dataspaces_entities.log", maxBytes=1000000, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if config.debug else logging.INFO)

    # Set formatters
    file_formatter = logging.Formatter(
        "[%(levelname)-8s %(asctime)s %(filename)s:%(lineno)d] %(message)s",
        "%d-%m-%Y %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    console_formatter = DefaultFormatter("%(levelprefix)s [%(name)s] %(message)s")
    console_handler.setFormatter(console_formatter)

    return [file_handler, console_handler]


def setup_logger() -> None:
    """Return a logger with the given name."""
    logger = logging.getLogger("dataspaces_entities")
    logger.setLevel(logging.DEBUG)

    for handler in _get_service_logger_handlers():
        logger.addHandler(handler)
