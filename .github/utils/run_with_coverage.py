"""Special file to run the application with coverage.

First, import the coverage module and start it.
Then, import the application factory, instantiate the application, to be run via `coverage_entrypoint.sh`,
and register a function to save the coverage at exit.
"""

from __future__ import annotations

import atexit

from coverage import Coverage

cov = Coverage(data_file=".coverage.docker", config_file="pyproject.toml")
cov.start()

from dataspaces_entities.main import create_app  # noqa: E402

app = create_app()


def save_coverage():
    print("saving coverage", flush=True)
    cov.stop()
    cov.save()


atexit.register(save_coverage)
