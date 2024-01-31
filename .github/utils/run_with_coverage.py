"""Special file to run the application with coverage.

First, import the coverage module and start it.
Then, import the application and register a function to save the coverage at exit.
Finally, run the application.
"""
from __future__ import annotations

import atexit

from coverage import Coverage

cov = Coverage(data_file=".coverage.docker", config_file="pyproject.toml")
cov.start()

from entities_service.main import APP  # noqa: F401, E402


def save_coverage():
    print("saving coverage", flush=True)
    cov.stop()
    cov.save()


atexit.register(save_coverage)
