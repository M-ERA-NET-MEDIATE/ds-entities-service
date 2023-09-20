#!/usr/bin/env python3
"""Run tests for the service."""
# pylint: disable=import-error
import argparse
import json
import os
import re
import sys
from typing import TYPE_CHECKING

import requests
from dlite import Instance
from pymongo import MongoClient

if TYPE_CHECKING:
    from typing import Any, Literal


DLITE_TEST_ENTITIES: "list[dict[str, Any]]" = [
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
    # SOFT5 example
    {
        "name": "Dog",
        "version": "0.1",
        "namespace": "http://onto-ns.com/meta",
        "description": "A dog.",
        "dimensions": [
            {
                "name": "ncolors",
                "description": "Number of different colors the dog has.",
            }
        ],
        "properties": [
            {
                "name": "name",
                "type": "string",
                "description": "The dog's name.",
            },
            {
                "name": "age",
                "type": "int",
                "description": "The dog's age.",
            },
            {
                "name": "color",
                "type": "string",
                "description": "The dog's different colors.",
                "dims": ["ncolors"],
            },
            {
                "name": "breed",
                "type": "string",
                "description": "The dog's breed.",
            },
        ],
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
    collection.insert_many(DLITE_TEST_ENTITIES)


def _get_version_name(uri: str) -> tuple[str, str]:
    """Return the version and name part of a uri."""
    match = re.match(
        r"^http://onto-ns\.com/meta/(?P<version>[^/]+)/(?P<name>[^/]+)$", uri
    )
    if match is None:
        raise RuntimeError("Could not retrieve version and name from test entities.")
    return match.group("version") or "", match.group("name") or ""


def _get_uri(entity: "dict[str, Any]") -> str:
    """Return the uri for an entity."""
    namespace = entity.get("namespace")
    version = entity.get("version")
    name = entity.get("name")
    if any(_ is None for _ in (namespace, version, name)):
        raise RuntimeError(
            "Could not retrieve namespace, version, and/or name from test entities."
        )
    return f"{namespace}/{version}/{name}"


def run_tests() -> None:
    """Test the service."""
    host = os.getenv("DOCKER_TEST_HOST", "localhost")
    port = os.getenv("DOCKER_TEST_PORT", "8000")
    for test_entity in DLITE_TEST_ENTITIES:
        uri = test_entity.get("uri")
        if uri is None:
            uri = _get_uri(test_entity)
        if not isinstance(uri, str):
            raise TypeError("uri must be a string")
        version, name = _get_version_name(uri)
        response = requests.get(f"http://{host}:{port}/{version}/{name}", timeout=5)
        assert response.ok, (
            f"Test data {uri!r} not found! (Or some other error).\n"
            f"Response:\n{json.dumps(response.json(), indent=2)}"
        )

        entity = response.json()
        assert entity == test_entity
        Instance.from_dict(test_entity)

    version, name = _get_version_name("http://onto-ns.com/meta/0.3/EntitySchema")
    response = requests.get(f"http://{host}:{port}/{version}/{name}", timeout=5)
    assert not response.ok, "Non existant (valid) URI returned an OK response!"
    assert (
        response.status_code == 404
    ), f"Response:\n\n{json.dumps(response.json(), indent=2)}"

    version, name = _get_version_name("http://onto-ns.com/meta/Entity/1.0")
    response = requests.get(f"http://{host}:{port}/{version}/{name}", timeout=5)
    assert not response.ok, "Invalid URI returned an OK response!"
    assert (
        response.status_code != 404
    ), f"Response:\n\n{json.dumps(response.json(), indent=2)}"


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
