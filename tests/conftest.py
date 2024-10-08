"""Configuration and fixtures for all pytest tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from pathlib import Path
    from typing import Any, Literal, Protocol, TypedDict

    from dataspaces_auth.fastapi._models import TokenData
    from fastapi.testclient import TestClient
    from httpx import Client

    from entities_service.models.auth import DSAPIRole
    from entities_service.service.backend.mongodb import MongoDBBackend

    class UserRoleDict(TypedDict):
        """Type for the user info dictionary with roles."""

        role: str
        db: str

    class UserDict(TypedDict):
        """Type for the user dictionary."""

        username: str
        password: str
        roles: list[UserRoleDict]

    class ClientFixture(Protocol):
        """Protocol for the client fixture."""

        def __call__(
            self,
            raise_server_exceptions: bool = True,
            allowed_role: (
                Literal["entities", "entities:read", "entities:write", "entities:edit", "entities:delete"]
                | None
            ) = None,
        ) -> TestClient | Client: ...

    class GetBackendUserFixture(Protocol):
        """Protocol for the get_backend_user fixture."""

        def __call__(self, auth_role: Literal["read", "write"] | None = None) -> UserDict: ...


class ParameterizeGetEntities(NamedTuple):
    """Returned tuple from parameterizing all entities."""

    entity: dict[str, Any]
    version: str
    name: str
    identity: str
    parsed_entity: dict[str, Any]


## Pytest configuration functions and hooks ##


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the command line option to run the tests with a live backend."""
    parser.addoption(
        "--live-backend",
        action="store_true",
        default=False,
        help="Run the tests with a live backend (real MongoDB).",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest - set DS_ENTITIES_SERVICE_BACKEND env var."""
    import os

    # These are only really (properly) used when running with --live-backend,
    # but it's fine to set them here, since they are not checked when running without.
    os.environ["DS_ENTITIES_SERVICE_X509_CERTIFICATE_FILE"] = "docker_security/test-client.pem"
    os.environ["DS_ENTITIES_SERVICE_CA_FILE"] = "docker_security/test-ca.pem"

    # Add extra markers
    config.addinivalue_line(
        "markers",
        "skip_if_live_backend: mark test to skip it if using a live backend, "
        "optionally specify a reason why it is skipped",
    )
    config.addinivalue_line(
        "markers",
        "skip_if_not_live_backend: mark test to skip it if not using a live backend, "
        "optionally specify a reason why it is skipped",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Called after collection has been performed. May filter or re-order the items
    in-place."""
    if config.getoption("--live-backend"):
        import os

        # If the tests are run with a live backend, do the following:
        # - skip the tests marked with 'skip_if_live_backend'
        # - add non-mocked hosts list to the httpx_mock marker
        prefix_reason = "Live backend used: {reason}"
        default_reason = "Test is skipped when using a live backend"
        for item in items:
            if "skip_if_live_backend" in item.keywords:
                marker: pytest.Mark = item.keywords["skip_if_live_backend"]

                if marker.args:
                    assert (
                        len(marker.args) == 1
                    ), "The 'skip_if_live_backend' marker can only have one argument."

                    reason = marker.args[0]
                elif marker.kwargs and "reason" in marker.kwargs:
                    reason = marker.kwargs["reason"]
                else:
                    reason = default_reason

                assert isinstance(reason, str), "The reason for skipping the test must be a string."

                # Add the skip marker to the test
                item.add_marker(pytest.mark.skip(reason=prefix_reason.format(reason=reason)))

            # HTTPX non-mocked hosts
            entities_service_port = os.getenv("DS_ENTITIES_SERVICE_PORT", "7000")
            non_mocked_hosts = ["localhost"]
            if entities_service_port:
                non_mocked_hosts.append(f"localhost:{entities_service_port}")

            # Handle the case of the httpx_mock marker already being present
            if "httpx_mock" in item.keywords:
                marker: pytest.Mark = item.keywords["httpx_mock"]

                # The marker already has non-mocked hosts - ignore
                if "non_mocked_hosts" in marker.kwargs:
                    continue

                # Add the non-mocked hosts to the marker
                item.add_marker(pytest.mark.httpx_mock(non_mocked_hosts=non_mocked_hosts))
            else:
                # Add the httpx_mock marker with the non-mocked hosts
                item.add_marker(pytest.mark.httpx_mock(non_mocked_hosts=non_mocked_hosts))
    else:
        # If the tests are not run with a live backend, skip the tests marked with
        # 'skip_if_not_live_backend'
        prefix_reason = "No live backend: {reason}"
        default_reason = "Test is skipped when not using a live backend"
        for item in items:
            if "skip_if_not_live_backend" in item.keywords:
                marker: pytest.Mark = item.keywords["skip_if_not_live_backend"]

                if marker.args:
                    assert (
                        len(marker.args) == 1
                    ), "The 'skip_if_not_live_backend' marker can only have one argument."

                    reason = marker.args[0]
                elif marker.kwargs and "reason" in marker.kwargs:
                    reason = marker.kwargs["reason"]
                else:
                    reason = default_reason

                assert isinstance(reason, str), "The reason for skipping the test must be a string."

                # The marker does not have a reason
                item.add_marker(pytest.mark.skip(reason=prefix_reason.format(reason=reason)))


def pytest_sessionstart(session: pytest.Session) -> None:
    """Called after the Session object has been created and before performing
    collection and entering the run test loop.

    Used together with `pytest_sessionfinish()` to:
    - Unpack and finally remove the `valid_entities.yaml` file to a
      `valid_entities/*.json` file set.
    - Temporarily rename a local `.env` file.

    """
    import json
    import shutil
    from pathlib import Path

    import yaml

    # Unpack `valid_entities.yaml` to `valid_entities/*.json`
    static_dir = (Path(__file__).parent / "static").resolve()

    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())

    valid_entities_dir = static_dir / "valid_entities"
    if valid_entities_dir.exists():
        raise FileExistsError(
            f"Will not unpack 'valid_entities.yaml' to '{valid_entities_dir}'. "
            "Directory already exists. Please deal with it manually."
        )

    valid_entities_dir.mkdir()

    for entity in entities:
        name: str | None = entity.get("name")
        if name is None:
            uri: str | None = entity.get("uri")
            if uri is None:
                raise ValueError("Could not retrieve neither uri and name from test entity.")
            name = uri.split("/")[-1]

        json_file = valid_entities_dir / f"{name}.json"
        if json_file.exists():
            raise FileExistsError(
                f"Could not unpack 'valid_entities.yaml' to '{json_file}'. File already exists."
            )

        json_file.write_text(json.dumps(entity))

    # Rename local '.env' file to '.env.temp_while_testing'
    if session.config.getoption("--live-backend"):
        # If the tests are run with a live backend, there is no need to rename the
        # local '.env' file
        return

    local_env_file = Path(session.startpath).resolve() / ".env"

    if local_env_file.exists():
        temporary_env_file = Path(session.startpath).resolve() / ".env.temp_while_testing"
        if temporary_env_file.exists():
            raise FileExistsError(
                "Could not temporarily rename local '.env' file to "
                f"'{temporary_env_file}'. File already exists."
            )

        shutil.move(local_env_file, temporary_env_file)

        if local_env_file.exists() or not temporary_env_file.exists():
            raise FileNotFoundError("Could not move local '.env' file to a temporary naming.")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    """Called after whole test run finished, right before returning the exit status to
    the system.

    Used together with `pytest_sessionstart()` to:
    - Unpack and finally remove the `valid_entities.yaml` file to a
      `valid_entities/*.json` file set.
    - Temporarily rename a local `.env` file.

    """
    import shutil
    from pathlib import Path

    # Remove `valid_entities/*.json`
    valid_entities_dir = (Path(__file__).parent / "static" / "valid_entities").resolve()

    if valid_entities_dir.exists():
        shutil.rmtree(valid_entities_dir)

    assert (
        not valid_entities_dir.exists()
    ), f"Could not remove '{valid_entities_dir}'. Directory still exists after removal."

    # Rename '.env.temp_while_testing' to '.env'
    if session.config.getoption("--live-backend"):
        # If the tests are run with a live backend, there is no need to return the
        # local '.env' file
        return

    local_env_file = Path(session.startpath).resolve() / ".env"

    if local_env_file.exists():
        raise FileExistsError(
            "The local '.env' file could not be returned to its original name "
            "because the file already exists."
        )

    temporary_env_file = Path(session.startpath).resolve() / ".env.temp_while_testing"
    if not temporary_env_file.exists():
        # The temporary file does not exist, so there is nothing to do
        return

    shutil.move(temporary_env_file, local_env_file)

    if not local_env_file.exists() or temporary_env_file.exists():
        raise FileNotFoundError(
            "Could not move local temporary '.env.temp_while_testing' file to the "
            "original '.env' naming."
        )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Return a parameterized entity."""
    if "parameterized_entity" not in metafunc.fixturenames:
        return

    import re
    from pathlib import Path

    import yaml

    def get_version_name(uri: str) -> tuple[str, str]:
        """Return the version and name part of a TEAM4.0-style URL."""
        namespace = "http://onto-ns.com/meta"

        match = re.match(rf"^{re.escape(namespace)}/(?P<version>[^/]+)/(?P<name>[^/]+)$", uri)
        assert match is not None, (
            f"Could not retrieve version and name from {uri!r}. "
            "URI must be of the form: "
            f"{namespace}/{{version}}/{{name}}\n\n"
            "Hint: The namespace part of the URI is hard-coded in the pytest configuration."
        )

        return match.group("version") or "", match.group("name") or ""

    def get_team40_url(entity: dict[str, Any]) -> str:
        """Return the TEAM4.0-style URL for an entity based on 'namespace', 'version', and 'name'."""
        namespace = entity.get("namespace")
        version = entity.get("version")
        name = entity.get("name")

        assert not any(
            _ is None for _ in (namespace, version, name)
        ), "Could not retrieve 'namespace', 'version', and/or 'name' from test entities."

        return f"{namespace}/{version}/{name}"

    results: list[ParameterizeGetEntities] = []

    static_dir = (Path(__file__).parent / "static").resolve()

    entities: list[dict[str, Any]] = yaml.safe_load((static_dir / "valid_entities.yaml").read_text())
    scrubbed_entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "valid_entities_soft7.yaml").read_text()
    )

    for index, entity in enumerate(entities):
        identity = entity.get("identity", entity.get("uri")) or get_team40_url(entity)

        version, name = get_version_name(identity)

        results.append(ParameterizeGetEntities(entity, version, name, identity, scrubbed_entities[index]))

    metafunc.parametrize(
        "parameterized_entity",
        results,
        ids=[f"{_.version}/{_.name}" for _ in results],
    )


## Pytest fixtures ##


@pytest.fixture(scope="session")
def live_backend(request: pytest.FixtureRequest) -> bool:
    """Return whether to run the tests with a live backend."""
    import os
    import warnings

    required_environment_variables = ("DS_ENTITIES_SERVICE_PORT",)

    value = request.config.getoption("--live-backend")

    # Check certain environment variables are set
    if value and any(os.getenv(_) is None for _ in required_environment_variables):
        with warnings.catch_warnings():
            warnings.simplefilter("default")
            warnings.warn(
                "All required environment variables were not found to be set. "
                "Please set the following environment variables: "
                f"{', '.join(required_environment_variables)}",
                stacklevel=1,
            )

    return value


@pytest.fixture(scope="session")
def static_dir() -> Path:
    """Return the path to the static directory."""
    from pathlib import Path

    return (Path(__file__).parent / "static").resolve()


@pytest.fixture(scope="session")
def get_backend_user() -> GetBackendUserFixture:
    """Return a function to get the backend user.

    This fixture implements a mock write user that wouldn't exist in production,
    since this auth level would be handled by TLS and a X.509 certificate.

    However, for testing, it is easier to do it this way using SCRAM.
    """
    from entities_service.service.config import CONFIG

    def _get_backend_user(auth_role: Literal["read", "write"] | None = None) -> UserDict:
        """Return the backend user for the given authentication role."""
        if auth_role is None:
            auth_role = "read"

        assert auth_role in (
            "read",
            "write",
        ), "The authentication role must be either 'read' or 'write'."

        if auth_role == "read":
            user: UserDict = {
                "username": CONFIG.mongo_user,
                "password": CONFIG.mongo_password.get_secret_value(),
                "roles": [
                    {
                        "role": "read",
                        "db": CONFIG.mongo_db,
                    }
                ],
            }
        else:  # write
            user: UserDict = {
                "username": "test_write_user",
                "password": "writer",
                "roles": [
                    {
                        "role": "readWrite",
                        "db": CONFIG.mongo_db,
                    }
                ],
            }

        return user

    return _get_backend_user


@pytest.fixture(scope="session", autouse=True)
def _mongo_backend_users(live_backend: bool, get_backend_user: GetBackendUserFixture) -> None:
    """Add MongoDB test users."""
    if not live_backend:
        return

    from entities_service.service.backend import get_backend

    backend: MongoDBBackend = get_backend(
        settings={
            "mongo_username": "root",
            "mongo_password": "root",
        },
    )
    admin_db = backend._collection.database.client["admin"]

    existing_users: list[str] = [
        user["user"] for user in admin_db.command("usersInfo", usersInfo=1)["users"]
    ]

    for auth_role in ("read", "write"):
        user_info = get_backend_user(auth_role)
        if user_info["username"] not in existing_users:
            admin_db.command(
                "createUser",
                createUser=user_info["username"],
                pwd=user_info["password"],
                roles=user_info["roles"],
            )


@pytest.fixture
def backend_test_data(static_dir: Path) -> list[dict[str, Any]]:
    """Return the test data for the backend."""
    import yaml

    return yaml.safe_load((static_dir / "valid_entities_soft7.yaml").read_text())


@pytest.fixture(autouse=True)
def _reset_mongo_test_collection(
    get_backend_user: GetBackendUserFixture,
    backend_test_data: list[dict[str, Any]],
    live_backend: bool,
) -> None:
    """Purge the MongoDB test collection."""
    if not live_backend:
        return

    from entities_service.service.backend import get_backend

    backend_user = get_backend_user("write")

    backend: MongoDBBackend = get_backend(
        auth_level="write",
        settings={
            "mongo_username": backend_user["username"],
            "mongo_password": backend_user["password"],
        },
    )
    backend._collection.delete_many({})
    backend._collection.insert_many(backend_test_data)


@pytest.fixture
def _empty_backend_collection(live_backend: bool, get_backend_user: GetBackendUserFixture) -> None:
    """Empty the backend collection."""
    if not live_backend:
        return

    from entities_service.service.backend import get_backend

    backend_user = get_backend_user("write")

    backend: MongoDBBackend = get_backend(
        auth_level="write",
        settings={
            "mongo_username": backend_user["username"],
            "mongo_password": backend_user["password"],
        },
    )
    backend._collection.delete_many({})
    assert backend._collection.count_documents({}) == 0


@pytest.fixture(autouse=True)
def _mock_lifespan(live_backend: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the MongoDBBackend.initialize() method."""
    # Only mock the lifespan context manager if the tests are not run with a live
    # backend
    if not live_backend:
        monkeypatch.setattr(
            "entities_service.service.backend.mongodb.MongoDBBackend.initialize",
            lambda _: None,
        )


@pytest.fixture
def client(live_backend: bool) -> ClientFixture:
    """Return the test client."""
    import os

    from fastapi.testclient import TestClient
    from httpx import Client

    def _create_mock_valid_access_token(
        allowed_role: DSAPIRole | str,
    ) -> Callable[[], Coroutine[Any, Any, TokenData]]:
        """Internal function to create a mock valid_access_token function with a specific set of roles.

        The roles are set by the `allowed_role` parameter and are all composite, with the exception of
        `entities:read`.

        The composite roles are:
        - `entities:write`
          Includes: `entities:read`
        - `entities:edit`
          Includes: `entities:write` and `entities:read`
        - `entities:delete`
          Includes: `entities:edit`, `entities:write`, and `entities:read`
        - `entities`
          Includes: `entities:delete`, `entities:edit`, `entities:write`, and `entities:read`

        """
        effective_roles: dict[str, list[str]] = {
            "entities:read": ["entities:read"],
            "entities:write": ["entities:write", "entities:read"],
            "entities:edit": ["entities:edit", "entities:write", "entities:read"],
            "entities:delete": ["entities:delete", "entities:edit", "entities:write", "entities:read"],
            "entities": ["entities", "entities:delete", "entities:edit", "entities:write", "entities:read"],
        }

        assert allowed_role in effective_roles, f"Invalid auth role: {allowed_role}"

        async def mock_valid_access_token() -> TokenData:
            """Mock the valid_access_token function from DataSpaces-Auth.

            Include all available roles for the entities service.
            """
            from dataspaces_auth.fastapi._models import TokenData

            return TokenData(
                # Role mapping
                resource_access={
                    "backend": {"roles": effective_roles[allowed_role]},
                    # Required resource_access field (for the model)
                    "account": {"roles": []},
                },
                # Required fields (for the model)
                preferred_username="test_user",
                iss="http://example.com",
                exp=1234567890,
                aud=["test_client"],
                sub="test_user",
                iat=1234567890,
                jti="test_jti",
            )

        return mock_valid_access_token

    def _client(
        raise_server_exceptions: bool = True,
        allowed_role: (
            Literal["entities", "entities:read", "entities:write", "entities:edit", "entities:delete"]
            | None
        ) = None,
    ) -> TestClient | Client:
        """Return the test client with the given authentication role."""
        if not live_backend:
            from dataspaces_auth.fastapi import valid_access_token

            from entities_service.main import APP

            # "entities:read" is the default role given to all users
            allowed_role = allowed_role or "entities:read"

            APP.dependency_overrides[valid_access_token] = _create_mock_valid_access_token(allowed_role)

            return TestClient(
                app=APP,
                raise_server_exceptions=raise_server_exceptions,
                follow_redirects=True,
            )

        port = os.getenv("DS_ENTITIES_SERVICE_PORT", "7000")

        base_url = f"http://localhost{':' + port if port else ''}"

        return Client(base_url=base_url, follow_redirects=True, timeout=10)

    return _client
