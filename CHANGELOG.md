# Changelog

## [Unreleased](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/tree/HEAD)

[Full Changelog](https://github.com/M-ERA-NET-MEDIATE/ds-entities-service/compare/v0.3.0...HEAD)

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
