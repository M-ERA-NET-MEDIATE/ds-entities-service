"""Configuration and fixtures for all pytest tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Literal, Protocol, TypedDict

    from fastapi.testclient import TestClient
    from httpx import Client
    from pytest_httpx import HTTPXMock

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
            auth_role: Literal["read", "write"] | None = None,
            raise_server_exceptions: bool = True,
        ) -> TestClient | Client: ...

    class GetBackendUserFixture(Protocol):
        """Protocol for the get_backend_user fixture."""

        def __call__(
            self, auth_role: Literal["read", "write"] | None = None
        ) -> UserDict: ...

    class MockAuthVerification(Protocol):
        """Protocol for the mock_auth_verification fixture."""

        def __call__(
            self, auth_role: Literal["read", "write"] | None = None
        ) -> None: ...


class ParameterizeGetEntities(NamedTuple):
    """Returned tuple from parameterizing all entities."""

    entity: dict[str, Any]
    version: str
    name: str
    uri: str
    backend_entity: dict[str, Any]


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
    """Configure pytest - set ENTITIES_SERVICE_BACKEND env var."""
    import os

    # These are only really (properly) used when running with --live-backend,
    # but it's fine to set them here, since they are not checked when running without.
    os.environ["ENTITIES_SERVICE_X509_CERTIFICATE_FILE"] = (
        "docker_security/test-client.pem"
    )
    os.environ["ENTITIES_SERVICE_CA_FILE"] = "docker_security/test-ca.pem"

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


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Called after collection has been performed. May filter or re-order the items
    in-place."""
    if config.getoption("--live-backend"):
        # If the tests are run with a live backend, skip the tests marked with
        # 'skip_if_live_backend'
        prefix_reason = "Live backend used: {reason}"
        default_reason = "Test is skipped when using a live backend"
        for item in items:
            if "skip_if_live_backend" in item.keywords:
                marker: pytest.Mark = item.keywords["skip_if_live_backend"]

                if marker.args:
                    assert len(marker.args) == 1, (
                        "The 'skip_if_live_backend' marker can only have one "
                        "argument."
                    )

                    reason = marker.args[0]
                elif marker.kwargs and "reason" in marker.kwargs:
                    reason = marker.kwargs["reason"]
                else:
                    reason = default_reason

                assert isinstance(
                    reason, str
                ), "The reason for skipping the test must be a string."

                # The marker does not have a reason
                item.add_marker(
                    pytest.mark.skip(reason=prefix_reason.format(reason=reason))
                )
    else:
        # If the tests are not run with a live backend, skip the tests marked with
        # 'skip_if_not_live_backend'
        prefix_reason = "No live backend: {reason}"
        default_reason = "Test is skipped when not using a live backend"
        for item in items:
            if "skip_if_not_live_backend" in item.keywords:
                marker: pytest.Mark = item.keywords["skip_if_not_live_backend"]

                if marker.args:
                    assert len(marker.args) == 1, (
                        "The 'skip_if_not_live_backend' marker can only have one "
                        "argument."
                    )

                    reason = marker.args[0]
                elif marker.kwargs and "reason" in marker.kwargs:
                    reason = marker.kwargs["reason"]
                else:
                    reason = default_reason

                assert isinstance(
                    reason, str
                ), "The reason for skipping the test must be a string."

                # The marker does not have a reason
                item.add_marker(
                    pytest.mark.skip(reason=prefix_reason.format(reason=reason))
                )


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

    entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "valid_entities.yaml").read_text()
    )

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
                raise ValueError(
                    "Could not retrieve neither uri and name from test entity."
                )
            name = uri.split("/")[-1]

        json_file = valid_entities_dir / f"{name}.json"
        if json_file.exists():
            raise FileExistsError(
                f"Could not unpack 'valid_entities.yaml' to '{json_file}'. File "
                "already exists."
            )

        json_file.write_text(json.dumps(entity))

    # Rename local '.env' file to '.env.temp_while_testing'
    if session.config.getoption("--live-backend"):
        # If the tests are run with a live backend, there is no need to rename the
        # local '.env' file
        return

    local_env_file = Path(session.startpath).resolve() / ".env"

    if local_env_file.exists():
        temporary_env_file = (
            Path(session.startpath).resolve() / ".env.temp_while_testing"
        )
        if temporary_env_file.exists():
            raise FileExistsError(
                "Could not temporarily rename local '.env' file to "
                f"'{temporary_env_file}'. File already exists."
            )

        shutil.move(local_env_file, temporary_env_file)

        if local_env_file.exists() or not temporary_env_file.exists():
            raise FileNotFoundError(
                "Could not move local '.env' file to a temporary naming."
            )


def pytest_sessionfinish(
    session: pytest.Session, exitstatus: int  # noqa: ARG001
) -> None:
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

    assert not valid_entities_dir.exists(), (
        f"Could not remove '{valid_entities_dir}'. "
        "Directory still exists after removal."
    )

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
    from copy import deepcopy
    from pathlib import Path

    import yaml

    def get_version_name(uri: str) -> tuple[str, str]:
        """Return the version and name part of a uri."""
        namespace = "http://onto-ns.com/meta"

        match = re.match(
            rf"^{re.escape(namespace)}/(?P<version>[^/]+)/(?P<name>[^/]+)$", uri
        )
        assert match is not None, (
            f"Could not retrieve version and name from {uri!r}. "
            "URI must be of the form: "
            f"{namespace}/{{version}}/{{name}}\n\n"
            "Hint: Did you (inadvertently) set the base_url to something?"
        )

        return match.group("version") or "", match.group("name") or ""

    def get_uri(entity: dict[str, Any]) -> str:
        """Return the uri for an entity."""
        namespace = entity.get("namespace")
        version = entity.get("version")
        name = entity.get("name")

        assert not any(
            _ is None for _ in (namespace, version, name)
        ), "Could not retrieve namespace, version, and/or name from test entities."

        return f"{namespace}/{version}/{name}"

    results: list[ParameterizeGetEntities] = []

    static_dir = (Path(__file__).parent / "static").resolve()

    entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "valid_entities.yaml").read_text()
    )

    for entity in entities:
        uri = entity.get("uri") or get_uri(entity)

        version, name = get_version_name(uri)

        # Replace $ref with ref
        backend_entity = deepcopy(entity)

        # SOFT5
        if isinstance(backend_entity["properties"], list):
            backend_entity["properties"] = [
                {key.replace("$ref", "ref"): value for key, value in property_.items()}
                for property_ in backend_entity["properties"]
            ]

        # SOFT7
        else:
            for property_name, property_value in list(
                backend_entity["properties"].items()
            ):
                backend_entity["properties"][property_name] = {
                    key.replace("$ref", "ref"): value
                    for key, value in property_value.items()
                }

        results.append(
            ParameterizeGetEntities(entity, version, name, uri, backend_entity)
        )

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

    required_environment_variables = (
        "ENTITIES_SERVICE_HOST",
        "ENTITIES_SERVICE_PORT",
    )

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

    def _get_backend_user(
        auth_role: Literal["read", "write"] | None = None
    ) -> UserDict:
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
def _mongo_backend_users(
    live_backend: bool, get_backend_user: GetBackendUserFixture
) -> None:
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


@pytest.fixture()
def backend_test_data(static_dir: Path) -> list[dict[str, Any]]:
    """Return the test data for the backend."""
    import yaml

    # Convert all '$ref' to 'ref' in the valid_entities.yaml file
    entities: list[dict[str, Any]] = yaml.safe_load(
        (static_dir / "valid_entities.yaml").read_text()
    )
    for entity in entities:
        # SOFT5
        if isinstance(entity["properties"], list):
            for index, property_value in enumerate(list(entity["properties"])):
                entity["properties"][index] = {
                    key.replace("$", ""): value for key, value in property_value.items()
                }

        # SOFT7
        elif isinstance(entity["properties"], dict):
            for property_name, property_value in list(entity["properties"].items()):
                entity["properties"][property_name] = {
                    key.replace("$", ""): value for key, value in property_value.items()
                }

        else:
            raise TypeError(
                f"Invalid type for entity['properties']: {type(entity['properties'])}"
            )

    return entities


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


@pytest.fixture()
def _empty_backend_collection(
    live_backend: bool, get_backend_user: GetBackendUserFixture
) -> None:
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


@pytest.fixture()
def token_mock() -> str:
    """Return a mock token."""
    return (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyb290IiwiaXNzIjoiaHR0cDovL29u"
        "dG8tbnMuY29tL21ldGEiLCJleHAiOjE3MDYxOTI1OTAsImNsaWVudF9pZCI6Imh0dHA6Ly9vbnRvL"
        "W5zLmNvbS9tZXRhIiwiaWF0IjoxNzA2MTkwNzkwfQ.FzvzWyI_CNrLkHhr4oPRQ0XEY8H9DL442QD"
        "8tM8dhVM"
    )


@pytest.fixture()
def auth_header(token_mock: str) -> dict[Literal["Authorization"], str]:
    """Return the authentication header."""
    from fastapi.security import HTTPAuthorizationCredentials

    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token_mock,
    )
    return {
        "Authorization": f"{mock_credentials.scheme} {mock_credentials.credentials}"
    }


@pytest.fixture()
def mock_auth_verification(
    httpx_mock: HTTPXMock,
    get_backend_user: GetBackendUserFixture,
    auth_header: dict[Literal["Authorization"], str],
) -> MockAuthVerification:
    """Mock authentication."""
    from entities_service.service.config import CONFIG

    # OpenID configuration
    httpx_mock.add_response(
        url=(
            f"{str(CONFIG.oauth2_provider).rstrip('/')}"
            "/.well-known/openid-configuration"
        ),
        json={
            "issuer": str(CONFIG.oauth2_provider).rstrip("/"),
            "authorization_endpoint": (
                f"{str(CONFIG.oauth2_provider).rstrip('/')}/oauth/authorize"
            ),
            "token_endpoint": f"{str(CONFIG.oauth2_provider).rstrip('/')}/oauth/token",
            "userinfo_endpoint": (
                f"{str(CONFIG.oauth2_provider).rstrip('/')}/oauth/userinfo"
            ),
            "jwks_uri": (
                f"{str(CONFIG.oauth2_provider).rstrip('/')}/oauth/discovery/keys"
            ),
            "response_types_supported": [
                "code",
            ],
            "subject_types_supported": [
                "public",
            ],
            "id_token_signing_alg_values_supported": [
                "RS256",
            ],
            "code_challenge_methods_supported": [
                "plain",
                "S256",
            ],
        },
    )

    def _mock_auth_verification(
        auth_role: Literal["read", "write"] | None = None
    ) -> None:
        """Mock authentication."""
        if auth_role is None:
            auth_role = "read"

        assert auth_role in (
            "read",
            "write",
        ), "The authentication role must be either 'read' or 'write'."

        backend_user = get_backend_user(auth_role)
        groups_role_developer = {
            "https://gitlab.org/claims/groups/developer": (
                [CONFIG.roles_group] if auth_role == "write" else []
            )
        }

        # Userinfo endpoint
        httpx_mock.add_response(
            url=f"{str(CONFIG.oauth2_provider).rstrip('/')}/oauth/userinfo",
            json={
                "sub": backend_user["username"],
                "name": backend_user["username"],
                "nickname": backend_user["username"],
                "preferred_username": backend_user["username"],
                "website": (
                    f"{str(CONFIG.oauth2_provider).rstrip('/')}"
                    f"/{backend_user['username']}"
                ),
                "profile": (
                    f"{str(CONFIG.oauth2_provider).rstrip('/')}"
                    f"/{backend_user['username']}"
                ),
                "picture": (
                    f"{str(CONFIG.oauth2_provider).rstrip('/')}"
                    f"/{backend_user['username']}"
                ),
                "groups": [CONFIG.roles_group],
                "https://gitlab.org/claims/groups/owner": [],
                "https://gitlab.org/claims/groups/maintainer": [],
                **groups_role_developer,
            },
            match_headers=auth_header,
        )

    return _mock_auth_verification


@pytest.fixture()
def client(
    live_backend: bool, auth_header: dict[Literal["Authorization"], str]
) -> ClientFixture:
    """Return the test client."""
    import os

    from fastapi.testclient import TestClient
    from httpx import Client

    from entities_service.main import APP

    def _client(
        auth_role: Literal["read", "write"] | None = None,
        raise_server_exceptions: bool = True,
    ) -> TestClient | Client:
        """Return the test client with the given authentication role."""
        if not live_backend:
            return TestClient(
                app=APP,
                raise_server_exceptions=raise_server_exceptions,
            )

        if auth_role is None:
            auth_role = "read"

        assert auth_role in ("read", "write"), (
            f"Invalid authentication role {auth_role!r}. Must be either 'read' or "
            "'write'."
        )

        host, port = os.getenv("ENTITIES_SERVICE_HOST", "localhost"), os.getenv(
            "ENTITIES_SERVICE_PORT", "8000"
        )

        base_url = f"http://{host}"

        if port:
            base_url += f":{port}"

        return Client(
            base_url=f"http://{host}:{port}",
            headers=auth_header,
        )

    return _client
