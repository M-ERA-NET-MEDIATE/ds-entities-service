# Service for serving DLite entities

This is a FastAPI-based REST API service running on onto-ns.com.
It's purpose is to serve DLite entities from an underlying database.

## Run the service

First, download and install the Python package from GitHub:

```shell
# Download (git clone)
git clone https://github.com/CasperWA/dlite-entities-service.git
cd dlite-entities-service

# Install (using pip)
python -m pip install -U pip
pip install -U -e .
```

### Using Docker

For development, start a local MongoDB server, e.g., through another Docker image:

```shell
docker run -d --name "mongodb" -p "27017:27017" mongo:6
```

Then build and run the DLite Entities Service Docker image:

```shell
docker build --pull -t entity-service --target development .
docker run --rm -d \
  --env "entity_service_mongo_uri=mongodb://localhost:27017" \
  --name "entity-service" \
  -p "8000:80" \
  entity-service
```

Now, fill up the MongoDB with valid DLite entities at the `dlite` database in the `entities` collection.

Then go to [localhost:8000/docs](http://localhost:8000/docs) and try out retrieving a DLite entity.

---

For production, use a public MongoDB, and follow the same instructions above for building and running the DLite Entities Service Docker image, but exchange the `--target` value with `production`, put in the proper value for the `entity_service_mongo_uri` environment value, possibly add the `entity_service_mongo_user` and `entity_service_mongo_password` environment variables as well, if needed.

### Using Docker Compose

Run the following commands:

```shell
docker compose pull
docker compose up --build
```

By default the `development` target will be built, to change this, set the `entity_service_docker_target` environment variable accordingly, e.g.:

```shell
entity_service_docker_target=production docker compose up --build
```

Furthermore, the used `localhost` port can be changed via the `PORT` environment variable.

### Using the local environment

Install an ASGI server, like `uvicorn`:

```shell
pip install uvicorn
```

Set some appropriate environment variables to ensure the service can hook up to a desired MongoDB.

Then run it according to your desires.
For example, in development, it might be nice to have the server reload if any files are changed, as well as the server logging debug messages:

```shell
uvicorn dlite_entities_service.main:APP --reload --host localhost --port 8000 --log-level debug --debug --no-server-header --header "Server:DLiteEntitiesService"
```

Then go to [localhost:8000/docs](http://localhost:8000/docs) and try out retrieving a DLite entity.

### Using a file for environment variables

The service supports a "dot-env" file, i.e., a `.env` file with a list of (secret) environment variables.

In order to use this, create a new file named `.env`.
This file will never be committed if you choose to `git commit` any files, as it has been hardcoded into the `.gitignore` file.

Then fill up the `.env` file with secret environment variables.

For using it locally, no changes are needed, as the service will automatically check for a `.env` file and load it in, using it to set the service app configuration.

For using it with Docker, use the `--env-file .env` argument when calling `docker run` or `docker compose up`.

## Licensing & copyright

All files in this repository are [MIT licensed](LICENSE).  
Copyright by [Casper Welzel Andersen](https://github.com/CasperWA).
