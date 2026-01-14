# Changelog

## [Unreleased](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/HEAD)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.6.0...HEAD)

## Better error responses

Custom exceptions and exception handlers ensure better error responses.
Instead of raising the generic `fastapi.HTTPException`, we now utilize FastAPI's (Starlette's) exception handler system to provide more explanatory custom exceptions in the code and better error message responses in the REST API.

## Check entity existence

Prior to creating new entities, it is checked whether the entity's URI/identity already exists in the database. If yes, then a `409 CONFLICT` HTTP response is returned. This is true if any of a list of entities to be created already exist.

## Miscellaneous

Update development tools and requirements.

**Implemented enhancements:**

- Check and return if entity exists for POST [\#132](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/132)

## [v0.6.0](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.6.0) (2026-01-05)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.5.2...v0.6.0)

## Better error responses

Custom exceptions and exception handlers ensure better error responses.
Instead of raising the generic `fastapi.HTTPException`, we now utilize FastAPI's (Starlette's) exception handler system to provide more explanatory custom exceptions in the code and better error message responses in the REST API.

## Check entity existence

Prior to creating new entities, it is checked whether the entity's URI/identity already exists in the database. If yes, then a `409 CONFLICT` HTTP response is returned. This is true if any of a list of entities to be created already exist.

## Miscellaneous

Update development tools and requirements.

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#188](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/188) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Custom exceptions and handlers [\#187](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/187) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#186](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/186) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#183](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/183) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.5.2](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.5.2) (2025-12-03)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.5.1...v0.5.2)

## Update dependencies and the developer experience (DX)

Several Python dependencies have had their minimum version updated.
The dev tools and CI/CD actions have been updated.

Deprecated parts from pydantic has been updated to non-deprecated parts.

**Closed issues:**

- Use DLite for Python 3.13 tests / Remove testing support for DLite [\#80](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/80)

**Merged pull requests:**

- Update minimum versions in `pyproject.toml` [\#178](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/178) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#177](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/177) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#176](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/176) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#172](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/172) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#171](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/171) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#170](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/170) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#168](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/168) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#165](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/165) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#163](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/163) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#162](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/162) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#161](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/161) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#159](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/159) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#158](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/158) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#156](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/156) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Fix typo [\#154](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/154) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#152](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/152) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#151](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/151) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#150](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/150) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#148](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/148) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#145](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/145) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#144](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/144) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#142](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/142) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#141](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/141) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#140](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/140) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#137](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/137) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#135](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/135) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#134](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/134) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#133](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/133) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#131](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/131) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#130](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/130) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#129](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/129) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update to latest DLite-Python [\#128](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/128) ([CasperWA](https://github.com/CasperWA))
- Drop safety in favor of pip-audit [\#127](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/127) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#125](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/125) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#123](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/123) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#120](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/120) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#117](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/117) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#115](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/115) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.5.1](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.5.1) (2025-03-04)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.5.0...v0.5.1)

## Loosen URI requirements

Defer to `s7.pydantic_models.soft7_entity.SOFT7IdentityURI` and its accompanying type for determining the validity of an entity's URI value.

Currently, the only requirement for the URI is to be a valid URL with either of the `http`, `https`, or `file` schemes.

## Update dependencies

Update various dependencies and dev. tools.

**Implemented enhancements:**

- Use SOFT7IdentityURI and type from s7 [\#112](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/112) ([CasperWA](https://github.com/CasperWA))

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#111](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/111) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#110](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/110) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#107](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/107) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#105](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/105) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#104](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/104) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.5.0](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.5.0) (2025-01-30)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.4.1...v0.5.0)

# Remove the need for an X.509 certificate

The need for a certificate between the service REST API and the underlying MongoDB is leftover from the origins of this repository. It originates from [SINTEF/entities-service](https://github.com/SINTEF/entities-service), which was meant to connect via an X.509 certificate to MongoDB Atlas. This is, however, not relevant for this re-implementation.

Removing this, also removes a lot of logic pertaining to different MongoDB-specific users, simplifying the code base significantly.

## QoL for DX

Dependencies and dev tools have been updated, along with the CI/CD workflows to accommodate the removal of extra MongoDB authentication.

**Implemented enhancements:**

- Remove extra security layers for MongoDB [\#95](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/95)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#100](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/100) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#97](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/97) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Remove X509 user and self-signed certificates [\#96](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/96) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#94](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/94) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#92](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/92) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#91](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/91) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.4.1](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.4.1) (2024-12-26)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.4.0...v0.4.1)

# Fit into DataSpaces-Services

Patch release to allow `httpx` v0.27.x, which is needed to support `httpx-auth` (at the moment).

**Merged pull requests:**

- Support httpx-auth by allowing v0.27.x of httpx [\#89](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/89) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#88](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/88) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#87](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/87) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#85](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/85) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.4.0](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.4.0) (2024-12-02)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.3.0...v0.4.0)

# Support Python 3.13

Test Python 3.13 in CI and add it as a supported version to the package metadata.

Note, [DLite](https://github.com/SINTEF/dlite) currently does not support Python 3.13, and so any functionality using DLite together with this package directly is not supported.

## Update dependencies

Update dependencies and developer tools (pre-commit hooks, etc.)

Support the latest [SOFT7](https://github.com/SINTEF/soft7) package, which together with local changes in the repository supports [pydantic](https://docs.pydantic.dev) v2.10, which has several breaking changes in the `networks` module.

**Implemented enhancements:**

- Test support for Python 3.13 [\#64](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/64)

**Closed issues:**

- Why do we need git in the docker container? Should we add a new development layer? [\#42](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/42)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#82](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/82) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#79](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/79) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#77](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/77) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#76](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/76) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#74](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/74) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#72](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/72) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Run pytest in CI with Python 3.13 [\#65](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/65) ([CasperWA](https://github.com/CasperWA))

## [v0.3.0](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.3.0) (2024-10-15)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.2.1...v0.3.0)

## Change package name and top-level import module

The package name has changed from `ds-entities-service` to `DataSpaces-Entities`.
The top-level package module has changed from `entities_service` to `dataspaces_entities`.

This is all done to differentiate this package (and repository) from its originator ([`entities-service`](https://github.com/SINTEF/entities-service)) as well as cementing it as part of the DataSpaces by SemanticMatter.

## Use DataSpaces-Auth for auth handling

The [DataSpaces-Auth package](https://gitlab.sintef.no/groups/semanticmatter/-/packages/?orderBy=created_at&sort=desc&search[]=DataSpaces-Auth) is utilized for OAuth2 handling of the service.
Specifically, it offers fine-grained access via OAuth2 "roles". This is offered through the `dataspaces_auth.fastapi.has_role` function, which can be used in any FastAPI application utilizing dependency injection.

The roles are defined in the `models` module, which reflect the actual roles as implemented in the DataSpaces Keycloak service.

## DX

Moving to use DataSpaces-Auth has led to a lot of code deletion, since all things to do with auth handling can be removed.

To show this closer relationship with the DataSpaces, the environment variable prefix to set settings has also been prepended with `DS_`. Moreover, the prefix has also dropped the `SERVICES_` part, so it is now: `DS_ENTITIES_`.

When using DataSpaces-Auth, it also offer pytest fixtures to handle authentication and authorization during testing. These have been implemented and utilized.

All dependencies and dev tools have been updated to support the latest version and install these as a minimum.

**Implemented enhancements:**

- Support DataSpaces-Auth v0.2.1 [\#63](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/63)
- Use exposed "public" pytest fixtures from DataSpaces-Auth [\#62](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/62)
- Update Python API [\#60](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/60)
- Add authentication roles to this repository \(and package\) [\#56](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/56)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#69](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/69) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update Python API [\#67](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/67) ([CasperWA](https://github.com/CasperWA))
- Use fixtures from DataSpaces-Auth [\#61](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/61) ([CasperWA](https://github.com/CasperWA))
- Remove all local auth handling [\#59](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/59) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#58](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/58) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#55](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/55) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#52](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/52) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.1](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.2.1) (2024-09-18)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.2.0...v0.2.1)

## Ensure v0.2.1 of `soft7` is used

Minor patch update to ensure at minimum v0.2.1 of the `soft7` package is used.

**Closed issues:**

- Exclude CHANGELOG from pre-commit hooks [\#48](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/48)

**Merged pull requests:**

- Exclude `CHANGELOG.md` from relevant pre-commit hooks [\#49](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/49) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#47](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/47) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.2.0](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.2.0) (2024-09-12)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.1.1...v0.2.0)

## Use `soft7` package for entity management

Use the [`soft7`](https://pypi.org/project/soft7) package to validate and handle entities. Specifically, exchange the local pydantic models with those defined in the `soft7` package.

**Important**: This introduces a "breaking" change. This means the `uri` (or now `identity`) value is no longer so strictly guarded and validated. There is now no error if the namespace or composition is malformed according to the TEAM4.0-style URLs, i.e., if the namespace does not start with `http://onto-ns.com/meta`.

### Miscellaneous

Update several development and support files.

**Implemented enhancements:**

- ✨ Use SOFT7 [\#34](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/34)

**Merged pull requests:**

- Use the `soft7` package [\#35](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/35) ([CasperWA](https://github.com/CasperWA))

## [v0.1.1](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.1.1) (2024-08-08)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.1.0...v0.1.1)

## First release from GitHub

This is the first release from GitHub, using the appropriate CD workflow.
It is a minor release, as the main difference with v0.1.0 is the addition/update of the CD workflow.

Since this package is based on [`entities-service`](https://github.com/SINTEF/entities-service) it is not released on PyPI, but rather it is available on SINTEF's GitLab instance, specifically through a dedicated MEDIATE project.

For those with access, information about the package can be found [here](https://gitlab.sintef.no/groups/semanticmatter/-/packages/9377).

**Closed issues:**

- Publish package on GitLab [\#29](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/29)

**Merged pull requests:**

- Publish Python package on SINTEF's GitLab [\#30](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/30) ([CasperWA](https://github.com/CasperWA))

## [v0.1.0](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/v0.1.0) (2024-08-07)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/aabe29f4aa4b20d4c2c3e1b46d0ad20467f6fbfb...v0.1.0)

**Implemented enhancements:**

- Remove use of mongomock [\#4](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/4)

**Fixed bugs:**

- Cap DLite version [\#17](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/issues/17)

**Merged pull requests:**

- DataSpaces integration [\#28](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/28) ([CasperWA](https://github.com/CasperWA))
- Fix test user creation in MongoDB [\#25](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/25) ([CasperWA](https://github.com/CasperWA))
- Update DLite and specify max major version for NumPy [\#18](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/18) ([CasperWA](https://github.com/CasperWA))
- Remove mongomock [\#5](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/5) ([CasperWA](https://github.com/CasperWA))
- New `/entities` router endpoints [\#3](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/pull/3) ([CasperWA](https://github.com/CasperWA))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
