"""Auth models."""

from __future__ import annotations

from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
)
from pydantic.networks import Url, UrlConstraints

AnyHttpsUrl = Annotated[Url, UrlConstraints(allowed_schemes=["https"])]


class OpenIDConfiguration(BaseModel):
    """OpenID configuration for Code flow with PKCE.

    This is defined in the OpenID Connect Discovery specification.
    Reference: https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata

    As well as the OAuth 2.0 Authorization Server Metadata [RFC8414].
    Reference: https://www.rfc-editor.org/rfc/rfc8414.html#section-2

    Note, the model only includes the fields required by the OpenID specification
    as well as those necessary for the Code flow with PKCE.
    """

    issuer: Annotated[
        AnyHttpsUrl,
        Field(
            description=(
                "URL using the `https` scheme with no query or fragment components "
                "that the OP asserts as its Issuer Identifier. If Issuer discovery is "
                "supported (see [Section 2](https://openid.net/specs/openid-connect"
                "-discovery-1_0.html#IssuerDiscovery)), this value MUST be identical "
                "to the issuer value returned by WebFinger. This also MUST be "
                "identical to the `iss` Claim value in ID Tokens issued from this "
                "Issuer."
            ),
        ),
    ]
    authorization_endpoint: Annotated[
        AnyHttpsUrl,
        Field(
            description=(
                "URL of the OP's OAuth 2.0 Authorization Endpoint [[OpenID.Core]]("
                "https://openid.net/specs/openid-connect-discovery-1_0.html#OpenID.Core"
                "). This URL MUST use the `https` scheme and MAY contain port, path, "
                "and query parameter components."
            ),
        ),
    ]
    token_endpoint: Annotated[
        AnyHttpsUrl,
        Field(
            description=(
                "URL of the OP's OAuth 2.0 Token Endpoint [[OpenID.Core]]("
                "https://openid.net/specs/openid-connect-discovery-1_0.html#OpenID.Core"
                "). This URL MUST use the `https` scheme and MAY contain port, path, "
                "and query parameter components."
            ),
        ),
    ]
    userinfo_endpoint: Annotated[
        AnyHttpsUrl | None,
        Field(
            description=(
                "URL of the OP's UserInfo Endpoint [[OpenID.Core]]("
                "https://openid.net/specs/openid-connect-discovery-1_0.html#OpenID.Core"
                "). This URL MUST use the `https` scheme and MAY contain port, path, "
                "and query parameter components."
            ),
        ),
    ] = None
    jwks_uri: Annotated[
        AnyHttpsUrl,
        Field(
            description=(
                "URL of the OP's JWK Set [[JWK]]("
                "https://openid.net/specs/openid-connect-discovery-1_0.html#JWK) "
                "document, which MUST use the `https` scheme. This contains the "
                "signing key(s) the RP uses to validate signatures from the OP. The "
                "JWK Set MAY also contain the Server's encryption key(s), which are "
                "used by RPs to encrypt requests to the Server. When both signing and "
                "encryption keys are made available, a `use` (public key use) "
                "parameter value is REQUIRED for all keys in the referenced JWK Set to "
                "indicate each key's intended usage. Although some algorithms allow "
                "the same key to be used for both signatures and encryption, doing so "
                "is NOT RECOMMENDED, as it is less secure. The JWK `x5c` parameter MAY "
                "be used to provide X.509 representations of keys provided. When used, "
                "the bare key values MUST still be present and MUST match those in the "
                "certificate. The JWK Set MUST NOT contain private or symmetric key "
                "values."
            ),
        ),
    ]
    response_types_supported: Annotated[
        list[str],
        Field(
            description=(
                "JSON array containing a list of the OAuth 2.0 `response_type` values "
                "that this OP supports. Dynamic OpenID Providers MUST support the "
                "`code`, `id_token`, and the `id_token` `token` Response Type values."
            ),
        ),
    ]
    subject_types_supported: Annotated[
        list[str],
        Field(
            description=(
                "JSON array containing a list of the Subject Identifier types that "
                "this OP supports. Valid types include `pairwise` and `public`."
            ),
        ),
    ]
    id_token_signing_alg_values_supported: Annotated[
        list[str],
        Field(
            description=(
                "JSON array containing a list of the JWS signing algorithms (`alg` "
                "values) supported by the OP for the ID Token to encode the Claims in "
                "a JWT [[JWT]](https://openid.net/specs/openid-connect-discovery-1_0"
                ".html#JWT). The algorithm `RS256` MUST be included. The value `none` "
                "MAY be supported but MUST NOT be used unless the Response Type used "
                "returns no ID Token from the Authorization Endpoint (such as when "
                "using the Authorization Code Flow)."
            ),
        ),
    ]
    code_challenge_methods_supported: Annotated[
        list[str] | None,
        Field(
            description=(
                "JSON array containing a list of Proof Key for Code Exchange (PKCE) "
                "[[RFC7636](https://www.rfc-editor.org/rfc/rfc7636)] code challenge "
                "methods supported by this authorization server.  Code challenge "
                "method values are used in the 'code_challenge_method' parameter "
                "defined in [Section 4.3 of [RFC7636]](https://www.rfc-editor.org/"
                "rfc/rfc7636#section-4.3). The valid code challenge method values are "
                "those registered in the IANA 'PKCE Code Challenge Methods' registry "
                "[[IANA.OAuth.Parameters](https://www.rfc-editor.org/rfc/rfc8414.html"
                "#ref-IANA.OAuth.Parameters)]. If omitted, the authorization server "
                "does not support PKCE."
            ),
        ),
    ] = None


class GitLabUserInfo(BaseModel):
    """OpenID userinfo response from GitLab.

    This is defined in the OpenID Connect specification.
    Reference: https://openid.net/specs/openid-connect-core-1_0.html#UserInfo

    Claims not defined in the OpenID Connect specification are prefixed with
    `https://gitlab.org/claims/`.
    As well as the `groups` claim, which is a list of groups the user is a member of.
    """

    sub: Annotated[
        str, Field(description="Subject - Identifier for the End-User at the Issuer.")
    ]
    name: Annotated[
        str | None,
        Field(
            description=(
                "End-User's full name in displayable form including all name parts, "
                "possibly including titles and suffixes, ordered according to the "
                "End-User's locale and preferences."
            ),
        ),
    ] = None
    preferred_username: Annotated[
        str | None,
        Field(
            description=(
                "Shorthand name by which the End-User wishes to be referred to at the "
                "RP, such as `janedoe` or `j.doe`. This value MAY be any valid JSON "
                "string including special characters such as `@`, `/`, or whitespace. "
                "The RP MUST NOT rely upon this value being unique, as discussed in "
                "[Section 5.7](https://openid.net/specs/openid-connect-core-1_0.html"
                "#ClaimStability)."
            ),
        ),
    ] = None
    groups: Annotated[
        list[str],
        Field(
            description=(
                "Paths for the groups the user is a member of, either directly or "
                "through an ancestor group."
            ),
        ),
    ] = []
    groups_owner: Annotated[
        list[str],
        Field(
            alias="https://gitlab.org/claims/groups/owner",
            description=(
                "Names of the groups the user is a direct member of with Owner role."
            ),
        ),
    ] = []
    groups_maintainer: Annotated[
        list[str],
        Field(
            alias="https://gitlab.org/claims/groups/maintainer",
            description=(
                "Names of the groups the user is a direct member of with Maintainer "
                "role."
            ),
        ),
    ] = []
    groups_developer: Annotated[
        list[str],
        Field(
            alias="https://gitlab.org/claims/groups/developer",
            description=(
                "Names of the groups the user is a direct member of with Developer "
                "role."
            ),
        ),
    ] = []
