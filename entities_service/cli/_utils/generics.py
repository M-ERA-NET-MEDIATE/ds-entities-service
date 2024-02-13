"""Various generic constants and functions used by the CLI."""

from __future__ import annotations

import difflib
import logging
import os
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import httpx
    import rich.pretty
    from httpx_auth import JsonTokenFileCache, OAuth2, OAuth2AuthorizationCodePKCE
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Please install the entities service utility CLI with 'pip install "
        f"{Path(__file__).resolve().parent.parent.parent.parent.resolve()}[cli]'"
    ) from exc

from httpx_auth import errors as auth_errors
from pydantic import ValidationError
from pydantic.networks import AnyHttpUrl
from rich import get_console
from rich import print as rich_print
from rich.console import Console

from entities_service.models.auth import OpenIDConfiguration

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, TextIO


EXC_MSG_INSTALL_PACKAGE = (
    "Please install the entities service utility CLI with "
    f"'pip install {Path(__file__).resolve().parent.parent.parent.parent.resolve()}"
    "[cli]' or 'pip install entities-service[cli]'"
)

OUTPUT_CONSOLE = get_console()
ERROR_CONSOLE = Console(stderr=True)

CACHE_DIRECTORY: Path = Path(
    os.getenv(
        "ENTITY_SERVICE_CLI_CACHE_DIR", str(Path.home() / ".cache" / "entities-service")
    )
).resolve()
"""The directory where the CLI caches data."""

LOGGER = logging.getLogger(__name__)

# Set OAuth2 configuration
OAuth2.token_cache = JsonTokenFileCache(
    str(CACHE_DIRECTORY / "oauth2_token_cache.json")
)
AuthenticationError = (
    auth_errors.AuthenticationFailed,
    auth_errors.InvalidToken,
    auth_errors.GrantNotProvided,
    auth_errors.StateNotProvided,
    auth_errors.TokenExpiryNotProvided,
    auth_errors.InvalidGrantRequest,
)
"""The exceptions that can be raised by the OAuth2 authentication flow."""
OPENID_CONFIG_URL = "https://gitlab.sintef.no/.well-known/openid-configuration"

# GitLab configuration
CLIENT_ID = "d96d899adfbe274e9f6d518d03d1ac036ad06c21a7f8e82812b8c0cc9a0a3477"


def print(
    *objects: Any,
    sep: str | None = None,
    end: str | None = None,
    file: TextIO | None = None,
    flush: bool | None = None,
) -> None:
    """Print to the output console."""
    file = file or OUTPUT_CONSOLE.file
    kwargs = {"sep": sep, "end": end, "file": file, "flush": flush}
    for key, value in list(kwargs.items()):
        if value is None:
            del kwargs[key]

    rich_print(*objects, **kwargs)


def pretty_compare_dicts(
    dict_first: dict[Any, Any], dict_second: dict[Any, Any]
) -> str:
    return "\n".join(
        difflib.ndiff(
            rich.pretty.pretty_repr(dict_first).splitlines(),
            rich.pretty.pretty_repr(dict_second).splitlines(),
        ),
    )


def initialize_oauth2(
    openid_config_url: str | None = None,
) -> OAuth2AuthorizationCodePKCE:
    """Create an OAuth2 authorization code flow."""
    if openid_config_url is None:
        openid_config_url = OPENID_CONFIG_URL

    try:
        openid_url: AnyHttpUrl = AnyHttpUrl(openid_config_url)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid OpenID configuration URL: {openid_config_url}."
            " Please check that the URL is correct."
        ) from exc

    try:
        with httpx.Client() as client:
            response: dict[str, Any] = client.get(openid_config_url).json()
    except (httpx.HTTPError, JSONDecodeError) as exc:
        raise ValueError(
            f"Could not retrieve OpenID configuration from {openid_config_url}."
            " Please check that the URL is correct."
        ) from exc

    try:
        openid_config = OpenIDConfiguration(**response)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid OpenID configuration from {openid_config_url}."
            " Please check that the URL is correct."
        ) from exc

    if openid_config.code_challenge_methods_supported is None:
        # If omitted, the authorization server does not support PKCE.
        raise ValueError(
            f"{openid_url.unicode_host} does not support the PKCE Auth flow."
        )

    response_type = "code"
    if response_type not in openid_config.response_types_supported:
        raise ValueError(
            f"Invalid response type {response_type!r}. Supported response types are: "
            f"{', '.join(openid_config.response_types_supported)}."
        )

    return OAuth2AuthorizationCodePKCE(
        authorization_url=str(openid_config.authorization_endpoint),
        token_url=str(openid_config.token_endpoint),
        redirect_uri_port=5666,  # redirect URL set on GitLab: http://localhost:5666/
        client_id=CLIENT_ID,
        scope="openid read_user",
    )


# OAuth2 authorization code flow
oauth = initialize_oauth2()
