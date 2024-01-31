"""Auth models."""

from __future__ import annotations

from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
)


class OpenIDConfiguration(BaseModel):
    """OpenID configuration for Code flow with PKCE."""

    issuer: AnyHttpUrl
    authorization_endpoint: AnyHttpUrl
    token_endpoint: AnyHttpUrl
    userinfo_endpoint: AnyHttpUrl | None = None
    jwks_uri: AnyHttpUrl
    registration_endpoint: AnyHttpUrl | None = None
    scopes_supported: list[str] | None = None
    response_types_supported: list[str]
    response_modes_supported: list[str] | None = None
    grant_types_supported: list[str] | None = None
    acr_values_supported: list[str] | None = None
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    id_token_encryption_alg_values_supported: list[str] | None = None
    id_token_encryption_enc_values_supported: list[str] | None = None
    userinfo_signing_alg_values_supported: list[str] | None = None
    userinfo_encryption_alg_values_supported: list[str] | None = None
    userinfo_encryption_enc_values_supported: list[str] | None = None
    request_object_signing_alg_values_supported: list[str] | None = None
    request_object_encryption_alg_values_supported: list[str] | None = None
    request_object_encryption_enc_values_supported: list[str] | None = None
    token_endpoint_auth_methods_supported: list[str] | None = None
    token_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    display_values_supported: list[str] | None = None
    claim_types_supported: list[str] | None = None
    claims_supported: list[str] | None = None
    service_documentation: AnyHttpUrl | None = None
    claims_locales_supported: list[str] | None = None
    ui_locals_supported: list[str] | None = None
    claims_parameter_supported: bool = False
    request_parameter_supported: bool = False
    request_uri_parameter_supported: bool = True
    require_request_uri_registration: bool = False
    op_policy_uri: AnyHttpUrl | None = None
    op_tos_uri: AnyHttpUrl | None = None
    code_challenge_methods_supported: list[str]

    # Extras
    revocation_endpoint: AnyHttpUrl | None = None
    introspection_endpoint: AnyHttpUrl | None = None


class GitLabUserInfo(BaseModel):
    """OpenID userinfo response from GitLab."""

    sub: str
    name: str
    nickname: str
    preferred_username: str
    email: str | None = None
    email_verified: bool | None = None
    website: AnyHttpUrl | str
    profile: AnyHttpUrl
    picture: AnyHttpUrl
    groups: list[str]
    groups_owner: Annotated[
        list[str], Field(alias="https://gitlab.org/claims/groups/owner")
    ] = []
    groups_maintainer: Annotated[
        list[str], Field(alias="https://gitlab.org/claims/groups/maintainer")
    ] = []
    groups_developer: Annotated[
        list[str], Field(alias="https://gitlab.org/claims/groups/developer")
    ] = []
