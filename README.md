<!-- markdownlint-disable MD013 -->
# DataSpaces service for serving Entities

This is a FastAPI-based REST API service meant to be used in DataSpaces.
It's purpose is to serve entities from a multitude of backends.

## Install the service

The service can be installed from SINTEF's GitLab:

```shell
pip install --index-url="https://gitlab.sintef.no/api/v4/projects/17883/packages/pypi/simple" DataSpaces-Entities
```

For development, we recommend cloning the repository and installing the package locally:

```shell
# Download (git clone)
git clone https://github.com/M-ERA-NET-MEDIATE/ds-entities-service.git
cd ds-entities-service

# Install (local clone)
pip install -U --index-url="https://gitlab.sintef.no/api/v4/projects/17883/packages/pypi/simple" -e .
```

> **Important**: If using this service locally alongside [DLite](https://github.com/SINTEF/dlite), it is important to note that issues may occur if [NumPy](https://numpy.org) v2 is used.
> There is no known issues with NumPy v1.
> This is a registered issue found for DLite v0.5.16.

## Run the service

The service requires a MongoDB server to be running, and the service needs to be able to connect to it.

### Using Docker and a local MongoDB server

For development, create a docker bridge network and start a local MongoDB server:

```shell
docker network create dataspaces_entities_net
docker run --rm -d \
  --env "MONGO_INITDB_ROOT_USERNAME=root" \
  --env "MONGO_INITDB_ROOT_PASSWORD=root" \
  --name "mongodb" \
  --publish "27017:27017" \
  --network "dataspaces_entities_net" \
  --volume "${PWD}/docker/docker_init/create_users.js:/docker-entrypoint-initdb.d/0_create_users.js" \
  mongo:8
```

Then build and run the DataSpaces-Entities service Docker image:

```shell
docker build --pull -t dataspaces-entities --target development .
docker run --rm -d \
  --env "DS_ENTITIES_MONGO_URI=mongodb://mongodb:27017" \
  --name "DataSpaces-Entities" \
  --user "${id -ur}:${id -gr}" \
  --publish "7000:80" \
  --network "dataspaces_entities_net" \
  dataspaces-entities
```

Now, fill up the MongoDB with valid entities at the `entities_service` database in the `entities` collection.

Then go to [localhost:7000/docs](http://localhost:7000/docs) and try out retrieving an entity.

### Using Docker Compose

Run the following commands:

```shell
docker compose pull
docker compose --env-file=.env up --build
```

By default the `production` target will be built, to change this, set the `DS_ENTITIES_DOCKER_TARGET` environment variable accordingly, e.g.:

```shell
DS_ENTITIES_DOCKER_TARGET=development docker compose --env-file=.env up --build
```

Or change the compose.yml file manually.

Furthermore, the used `localhost` port can be changed via the `DS_ENTITIES_PORT` environment variable.

The `--env-file` argument is optional, but if used, it should point to a file containing the environment variables needed by the service.
See the section on [using a file for environment variables](#using-a-file-for-environment-variables) for more information.

### Using a file for environment variables

The service supports a "dot-env" file, i.e., a `.env` file with a list of (secret) environment variables.

In order to use this, create a new file named `.env`.
This file will never be committed if you choose to `git commit` any files, as it has been hardcoded into the `.gitignore` file.

Fill up the `.env` file with (secret) environment variables.

For using it locally, no changes are needed, as the service will automatically check for a `.env` file and load it in, using it to set the service app configuration.

For using it with Docker, use the `--env-file .env` argument when calling `docker run` or `docker compose up`.

## Testing

The service is tested using `pytest` and can be tested against a local MongoDB server and DataSpaces-Entities service instance.

To run the tests, first install the test dependencies:

```shell
pip install -U -e .[testing]
```

To run the tests against a live backend, you can pull, build, and run the [Docker Compose file](compose.yml):

```shell
cd docker
docker compose pull
docker compose build
```

Then run (up) the Docker Compose file and subsequently the tests:

```shell
cd docker
docker compose up -d
cd ..
pytest --live-backend
```

> **Warning**: Setting `DS_ENTITIES_DISABLE_AUTH_ROLE_CHECKS=1` will effectively deactivate the OAuth2 authentication and user role checks and should only be used for testing purposes.

### Extra pytest markers

There are some custom pytest markers:

- `skip_if_live_backend`: skips the test if the `--live-backend` flag is set.
  Add this marker to tests that should not be run against a live backend.
  Either because they are not relevant for a live backend, or because they currently impossible to replicate within a live backend.

  A reason can be specified as an argument to the marker, e.g.:

  ```python
  @pytest.mark.skip_if_live_backend(reason="Cannot force an HTTP error")
  def test_something():
      ...
  ```

  **Availability**: This marker is available for all tests.

- `skip_if_not_live_backend`: skips the test if the `--live-backend` flag is **not** set.
  Add this marker to tests that should only be run against a live backend.
  Mainly due to the fact that the mock backend does not support the test.

  A reason can be specified as an argument to the marker, e.g.:

  ```python
  @pytest.mark.skip_if_not_live_backend(reason="OAuth2 cannot be mocked from the real backend")
  def test_something():
      ...
  ```

  **Availability**: This marker is available for all tests.

### Extra pytest fixtures

There is one fixture that may be difficult to locate, this is the `parameterized_entity` fixture.
It can be invoked to automatically parameterize a test, iterating over all the valid entities that exist in the [`valid_entities.yaml`](tests/static/valid_entities.yaml) static test file.
It will return one of these entities as a parsed dictionary for each iteration, i.e., within each test.

The fixture is available for all tests.

## Licensing & copyright

All files in this repository are [MIT licensed](LICENSE).  
Copyright by [Casper Welzel Andersen](https://github.com/CasperWA), [SINTEF](https://www.sintef.no).
