#!/usr/bin/env python3
"""Run tests for the service."""
import argparse
import os
import re
import sys
from typing import TYPE_CHECKING

import requests
from dlite import Instance
from pymongo import MongoClient

if TYPE_CHECKING:
    from typing import Literal


DLITE_TEST_ENTITIES = [
    {
        "uri": "http://onto-ns.com/meta/0.1/Person",
        "meta": "http://onto-ns.com/meta/0.3/EntitySchema",
        "description": "A person.",
        "dimensions": {"nskills": "Number of skills."},
        "properties": {
            "name": {
                "type": "string",
                "description": "The person's name.",
            },
            "age": {
                "type": "int",
                "description": "The person's age.",
            },
            "skills": {
                "type": "string",
                "description": "The person's skills.",
                "shape": ["nskills"],
            },
        },
    },
    {
        "uri": "http://onto-ns.com/meta/0.1/Cat",
        "meta": "http://onto-ns.com/meta/0.3/EntitySchema",
        "description": "A cat.",
        "dimensions": {"ncolors": "Number of different colors the cat has."},
        "properties": {
            "name": {
                "type": "string",
                "description": "The cat's name.",
            },
            "age": {
                "type": "int",
                "description": "The cat's age.",
            },
            "color": {
                "type": "string",
                "description": "The cat's different colors.",
                "shape": ["ncolors"],
            },
            "breed": {
                "type": "string",
                "description": "The cat's breed.",
            },
        },
    },
]


def add_testdata() -> None:
    """Add MongoDB test data."""
    mongodb_user = os.getenv("entity_service_mongo_user")
    mongodb_pass = os.getenv("entity_service_mongo_password")
    mongodb_uri = os.getenv("entity_service_mongo_uri")
    if any(_ is None for _ in (mongodb_user, mongodb_pass, mongodb_uri)):
        raise ValueError(
            "'entity_service_mongo_uri', 'entity_service_mongo_user', and "
            "'entity_service_mongo_password' environment variables MUST be specified."
        )

    client = MongoClient(mongodb_uri, username=mongodb_user, password=mongodb_pass)
    collection = client.dlite.entities

    for test_entity in DLITE_TEST_ENTITIES:
        collection.insert_one(test_entity)


def _get_version_name(uri: str) -> tuple[str, str]:
    """Return the version and name part of a uri."""
    match = re.match(
        r"^http://onto-ns\.com/meta/(?P<version>[^/]+)/(?P<name>[^/]+)$", uri
    )
    if match is None:
        raise RuntimeError("Could not retrieve version and name from test entities.")
    return match.group("version") or "", match.group("name") or ""


def run_tests() -> None:
    """Test the service."""
    host = os.getenv("DOCKER_TEST_HOST", "localhost")
    port = os.getenv("DOCKER_TEST_PORT", "8000")
    for test_entity in DLITE_TEST_ENTITIES:
        uri = test_entity["uri"]
        if not isinstance(uri, str):
            raise TypeError("uri must be a string")
        version, name = _get_version_name(uri)
        response = requests.get(f"http://{host}:{port}/{version}/{name}", timeout=5)
        assert (
            response.ok
        ), f"Test data {test_entity['uri']!r} not found! (Or some other error)"

        entity = response.json()
        assert entity == test_entity
        Instance.from_dict(test_entity)

    version, name = _get_version_name("http://onto-ns.com/meta/0.3/EntitySchema")
    response = requests.get(f"http://{host}:{port}/{version}/{name}", timeout=5)
    assert not response.ok, "Non existant (valid) URI returned an OK response!"
    assert response.status_code == 404

    version, name = _get_version_name("http://onto-ns.com/meta/Entity/1.0")
    response = requests.get(f"http://{host}:{port}/{version}/{name}", timeout=5)
    assert not response.ok, "Invalid URI returned an OK response!"
    assert response.status_code != 404


def main(args: list[str] | None = None) -> None:
    """Entrypoint for docker CI tests."""
    parser = argparse.ArgumentParser(
        prog="docker_test.py",
        description=main.__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "job",
        choices=["add-testdata", "run-tests"],
        default="run_tests",
    )

    job: 'Literal["add-testdata","run-tests"]' = parser.parse_args(args).job

    if job == "add-testdata":
        add_testdata()
    elif job == "run-tests":
        run_tests()
    else:
        raise ValueError(f"{job!r} isn't a valid input.")


if __name__ == "__main__":
    main(sys.argv[1:])
