"""Setup logging for DataSpaces-Entities."""

from __future__ import annotations

import logging.config

from dataspaces_auth import auth_logging_dict_config

from dataspaces_entities.config import get_config


def setup_logging():
    """Setup DataSpaces Python logging."""
    settings = get_config()

    logging_dict = auth_logging_dict_config(settings=settings)

    # Ensure top-level settings are as expected
    logging_dict.update({"version": 1, "disable_existing_loggers": False})

    # Add default (Uvicorn-style) formatter
    if "formatters" not in logging_dict:
        logging_dict["formatters"] = {}
    if "default_uvicorn" not in logging_dict["formatters"]:
        logging_dict["formatters"]["default_uvicorn"] = {
            "()": "dataspaces_auth._logging.DefaultFormatter",
            "fmt": "%(levelprefix)s [%(name)s] %(message)s",
        }

    # Add console handler
    if "handlers" not in logging_dict:
        logging_dict["handlers"] = {}
    if "console" not in logging_dict["handlers"]:
        logging_dict["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "default_uvicorn",
            "stream": "ext://sys.stdout",
            "level": "DEBUG" if settings.debug else "INFO",
        }

    if "loggers" not in logging_dict:
        logging_dict["loggers"] = {}

    # Add the DataSpaces Entities API logger
    logging_dict["loggers"]["dataspaces_entities"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

    logging.config.dictConfig(logging_dict)
