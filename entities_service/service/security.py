"""A security module for the Entities Service.

This module contains functions for authentication and authorization.
"""
from __future__ import annotations

import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient, HTTPError
from pydantic import ValidationError

from entities_service.models.auth import (
    GitLabUserInfo,
    OpenIDConfiguration,
)
from entities_service.service.config import CONFIG

if TYPE_CHECKING:  # pragma: no cover
    pass

# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SECURITY_SCHEME = HTTPBearer()

LOGGER = logging.getLogger(__name__)


async def get_openid_config() -> OpenIDConfiguration:
    """Get the OpenID configuration."""
    async with AsyncClient() as client:
        try:
            response = await client.get(
                f"{str(CONFIG.oauth2_provider).rstrip('/')}"
                "/.well-known/openid-configuration"
            )
        except HTTPError as exc:
            raise ValueError("Could not get OpenID configuration.") from exc

    try:
        return OpenIDConfiguration(**response.json())
    except (JSONDecodeError, ValidationError) as exc:
        raise ValueError("Could not parse OpenID configuration.") from exc


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(SECURITY_SCHEME)]
) -> None:
    """Verify a client user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials.credentials:
        raise credentials_exception

    try:
        openid_config = await get_openid_config()
    except ValueError as exc:
        LOGGER.error("Could not get OpenID configuration.")
        LOGGER.exception(exc)
        raise credentials_exception from exc

    if openid_config.userinfo_endpoint is None:
        LOGGER.error("OpenID configuration does not contain a userinfo endpoint.")
        raise credentials_exception

    async with AsyncClient() as client:
        try:
            response = await client.get(
                str(openid_config.userinfo_endpoint),
                headers={
                    "Authorization": f"{credentials.scheme} {credentials.credentials}"
                },
            )
        except HTTPError as exc:
            LOGGER.error("Could not get user info from OAuth2 provider.")
            LOGGER.exception(exc)
            raise credentials_exception from exc

    try:
        userinfo = GitLabUserInfo(**response.json())
    except (JSONDecodeError, ValidationError) as exc:
        LOGGER.error("Could not parse user info from OAuth2 provider.")
        LOGGER.exception(exc)
        raise credentials_exception from exc

    if CONFIG.roles_group not in userinfo.groups:
        LOGGER.error("User is not a member of the entities-service group.")
        credentials_exception.status_code = status.HTTP_403_FORBIDDEN
        credentials_exception.detail = (
            "You are not a member of the entities-service group. "
            "Please contact the entities-service group maintainer."
        )
        raise credentials_exception

    if not any(
        CONFIG.roles_group in group
        for group in [
            userinfo.groups_owner,
            userinfo.groups_maintainer,
            userinfo.groups_developer,
        ]
    ):
        LOGGER.error(
            "User does not have the rights to create entities. "
            "Hint: Change %s's role in the GitLab group %r",
            userinfo.preferred_username,
            CONFIG.roles_group,
        )
        credentials_exception.status_code = status.HTTP_403_FORBIDDEN
        credentials_exception.detail = (
            "You do not have the rights to create entities. "
            "Please contact the entities-service group maintainer."
        )
        raise credentials_exception
