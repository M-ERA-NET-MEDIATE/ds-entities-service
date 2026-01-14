FROM python:3.12-slim AS base

# Prevent writing .pyc files on the import of source modules.
# Set unbuffered mode to ensure logging outputs.
# Ignore root user actions for pip.
# Set the index URL to the SINTEF GitLab package registry for MEDIATE.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_ROOT_USER_ACTION="ignore"

# Set working directory
WORKDIR /app

# Install core system requirements
RUN apt-get -qqy update && apt-get -fqqy upgrade && \
  apt-get install --no-install-recommends -fqqy procps && \
  apt-get -qqy autoremove && apt-get -qqy clean && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY dataspaces_entities dataspaces_entities/
COPY asgi.py ./

# Install Python dependencies
RUN --mount=type=bind,source=docker/requirements.txt,target=/tmp/requirements.txt \
    pip install -q --no-cache-dir --upgrade pip setuptools wheel && \
    pip install -q -r /tmp/requirements.txt

ENTRYPOINT [ "gunicorn", "asgi:app", "--bind=0.0.0.0:80", "--workers=1", "--worker-class=dataspaces_entities.uvicorn.UvicornWorker" ]
EXPOSE 80

# Remove unnecessary files
RUN rm -rf ${HOME}/.cache /tmp/**

################# DEVELOPMENT ####################################
FROM base AS development

# Set debug mode, since we're running in development mode
ENV DS_ENTITIES_DEBUG=true

# Run with reload and debug log level
CMD [ "--log-level", "debug", "--reload" ]

################# PRODUCTION #####################################
FROM base AS production

# Force debug mode to be off, since we're running in production mode
ENV DS_ENTITIES_DEBUG=false
