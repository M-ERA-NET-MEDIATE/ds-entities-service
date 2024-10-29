FROM python:3.12-slim AS base

# Prevent writing .pyc files on the import of source modules.
# Set unbuffered mode to ensure logging outputs.
# Ignore root user actions for pip.
# Set the index URL to the SINTEF GitLab package registry for MEDIATE.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_ROOT_USER_ACTION="ignore"
ENV PIP_INDEX_URL="https://gitlab.sintef.no/api/v4/projects/17883/packages/pypi/simple"

# Set working directory
WORKDIR /app

# Install core system requirements
RUN apt-get -qqy update && apt-get -fqqy upgrade && \
  apt-get install --no-install-recommends -fqqy procps

# Copy the source code
COPY dataspaces_entities dataspaces_entities/
COPY asgi.py ./

# Install Python dependencies
RUN --mount=type=bind,source=README.md,target=/app/README.md \
    --mount=type=bind,source=LICENSE,target=/app/LICENSE \
    --mount=type=bind,source=pyproject.toml,target=/app/pyproject.toml \
    pip install -q --no-cache-dir --upgrade pip setuptools wheel && \
    pip install -q -e .[server]

ENTRYPOINT [ "gunicorn", "asgi:app", "--bind=0.0.0.0:80", "--workers=1", "--worker-class=dataspaces_entities.uvicorn.UvicornWorker" ]
EXPOSE 80

################# DEVELOPMENT ####################################
FROM base AS development

# Install system requirements for dev tools
RUN apt-get -qqy update && \
    apt-get install --no-install-recommends -fqqy git git-lfs && \
    apt-get -qqy autoremove && apt-get -qqy clean && rm -rf /var/lib/apt/lists/*

# Install additional development tools in virtual environment
RUN --mount=type=bind,source=docker/requirements_development.txt,target=/tmp/requirements_dev.txt \
    pip -m venv /tmp/dev_venv && \
    /tmp/dev_venv/bin/pip install -q --no-cache-dir --upgrade pip setuptools wheel && \
    /tmp/dev_venv/bin/pip install -q -r /tmp/requirements_dev.txt

# Run static security check and linters
RUN --mount=type=bind,source=docker/.pre-commit-config_docker.yaml,target=/app/.pre-commit-config.yaml \
    --mount=type=cache,target=${HOME}/.cache/pre-commit \
    git init && git add . && /tmp/dev_venv/bin/pre-commit run --all-files || ( cat ${HOME}/.cache/pre-commit/pre-commit.log && exit 1 )
RUN --mount=type=bind,source=docker/pyproject_requirements.txt,target=/tmp/requirements.txt \
    /tmp/dev_venv/bin/safety check -r /tmp/requirements.txt --full-report

# Copy over the self-signed certificates for development
COPY docker_security docker_security/

# Clean up
RUN rm -rf ${HOME}/.cache /tmp/* /app/.git && pip cache purge

# Set debug mode, since we're running in development mode
ENV DS_ENTITIES_DEBUG=1

CMD [ "--log-level=debug", "--reload" ]

################# PRODUCTION #####################################
FROM base AS production

# Force debug mode to be off, since we're running in production mode
ENV DS_ENTITIES_DEBUG=0

# Remove unnecessary files
RUN rm -rf ${HOME}/.cache /tmp/* && \
    apt-get -qqy autoremove && apt-get -qqy clean && rm -rf /var/lib/apt/lists/* && \
    pip cache purge
