<!-- markdownlint-disable MD013 -->
# DataSpaces service for serving Entities

This is a FastAPI-based REST API service meant to be used in DataSpaces.
It's purpose is to serve entities from a multitude of backends.

## Install the service

First, download and install the Python package from GitHub:

```shell
# Download (git clone)
git clone https://github.com/M-ERA-NET-MEDIATE/ds-entities-service.git
cd ds-entities-service

# Install (using pip)
python -m pip install -U pip
pip install -U -e .
```

## Run the service

The service requires a MongoDB server to be running, and the service needs to be able to connect to it.
The service also requires a valid X.509 certificate, in order to connect to the MongoDB server.

The MongoDB server could be on MongoDB Atlas, a local MongoDB server running either as a system service or through a Docker container.

### Using the local environment and MongoDB Atlas

First, create a MongoDB Atlas cluster, and a user with read-only access to the `entities` database.

Set the necessary environment variables:

```shell
ENTITIES_SERVICE_MONGO_URI=<your MongoDB Atlas URI>
ENTITIES_SERVICE_X509_CERTIFICATE_FILE=<your X.509 certificate file>
ENTITIES_SERVICE_MONGO_USER=<your MongoDB Atlas user with read-only access (default: 'guest')>
ENTITIES_SERVICE_MONGO_PASSWORD=<your MongoDB Atlas user's password with read-only access (default: 'guest')>
```

Run the service:

```shell
uvicorn entities_service.main:APP \
--host localhost \
--port 8000 \
--no-server-header \
--header "Server:EntitiesService"
```

Finally, go to [localhost:8000/docs](http://localhost:8000/docs) and try out retrieving an entity.

`--log-level debug` can be added to the `uvicorn` command to get more verbose logging.
`--reload` can be added to the `uvicorn` command to enable auto-reloading of the service when any files are changed.

Note, the environment variables can be set in a `.env` file, see the section on [using a file for environment variables](#using-a-file-for-environment-variables).

### Using Docker and a local MongoDB server

First, we need to create self-signed certificates for the service to use.
This is done by running the following command:

```shell
mkdir docker_security
cd docker_security
../.github/docker_init/setup_mongo_security.sh
```

Note, this is only possible with `openssl` installed on your system.
And the OS on the system being Linux/Unix-based.

For development, start a local MongoDB server, e.g., through another Docker image:

```shell
docker run --rm -d \
  --env "IN_DOCKER=true" \
  --env "HOST_USER=${USER}" \
  --env "MONGO_INITDB_ROOT_USERNAME=root" \
  --env "MONGO_INITDB_ROOT_PASSWORD=root" \
  --name "mongodb" \
  -p "27017:27017" \
  -v "${PWD}/.github/docker_init/create_x509_user.js:/docker-entrypoint-initdb.d/0_create_x509_user.js" \
  -v "${PWD}/docker_security:/mongo_tls" \
  mongo:7 \
  --tlsMode allowTLS --tlsCertificateKeyFile /mongo_tls/test-server1.pem --tlsCAFile /mongo_tls/
```

Then build and run the Entities Service Docker image:

```shell
docker build --pull -t ds-entities-service --target development .
docker run --rm -d \
  --env "ENTITIES_SERVICE_MONGO_URI=mongodb://localhost:27017" \
  --env "ENTITIES_SERVICE_X509_CERTIFICATE_FILE=docker_security/test-client.pem" \
  --env "ENTITIES_SERVICE_CA_FILE=docker_security/test-ca.pem" \
  --name "ds-entities-service" \
  -u "${id -ur}:${id -gr}" \
  -p "8000:80" \
  ds-entities-service
```

Now, fill up the MongoDB with valid entities at the `entities_service` database in the `entities` collection.

Then go to [localhost:8000/docs](http://localhost:8000/docs) and try out retrieving an entity.

---

For production, use a public MongoDB, and follow the same instructions above for building and running the Entities Service Docker image, but exchange the `--target` value with `production`, put in the proper value for the `ENTITIES_SERVICE_MONGO_URI` and `ENTITIES_SERVICE_X509_CERTIFICATE_FILE` environment values, possibly add the `ENTITIES_SERVICE_MONGO_USER`, `ENTITIES_SERVICE_MONGO_PASSWORD`, and `ENTITIES_SERVICE_CA_FILE` environment variables as well, if needed.

### Using Docker Compose

Run the following commands:

```shell
docker compose pull
docker compose --env-file=.env up --build
```

By default the `development` target will be built, to change this, set the `ENTITIES_SERVICE_DOCKER_TARGET` environment variable accordingly, e.g.:

```shell
ENTITIES_SERVICE_DOCKER_TARGET=production docker compose --env-file=.env up --build
```

Furthermore, the used `localhost` port can be changed via the `PORT` environment variable.

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

The service is tested using `pytest` and can be tested against a local MongoDB server and Entities Service instance.

To run the tests, first install the test dependencies:

```shell
pip install -U -e .[testing]
```

To run the tests against a live backend, you can pull, build, and run the [Docker Compose file](docker-compose.yml):

```shell
docker compose pull
docker compose build
```

Before running the services the self-signed certificates need to be created.
See the section on [using Docker and a local MongoDB server](#using-docker-and-a-local-mongodb-server) for more information.

Then run (up) the Docker Compose file and subsequently the tests:

```shell
docker compose up -d
pytest --live-backend
```

Remember to set the following environment variables:

- `ENTITIES_SERVICE_X509_CERTIFICATE_FILE=docker_security/test-server1.pem`
- `ENTITIES_SERVICE_CA_FILE=docker_security/test-ca.pem`
- `ENTITIES_SERVICE_DEACTIVATE_OAUTH=1`

> **Warning** Setting `ENTITIES_SERVICE_DEACTIVATE_OAUTH` will deactivate the OAuth2 authentication and should only be used for testing purposes.

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
