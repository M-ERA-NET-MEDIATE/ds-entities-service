FROM python:3.10 as base

WORKDIR /app

COPY entities_service entities_service/
COPY pyproject.toml LICENSE README.md ./

# Install dependencies
RUN python -m pip install -U pip && \
  pip install -U setuptools wheel && \
  pip install -U -e .[server]

## DEVELOPMENT target
FROM base as development

# Copy over the self-signed certificates for development
COPY docker_security docker_security/

ENV PORT=80
EXPOSE ${PORT}

# Set debug mode, since we're running in development mode
ENV ENTITIES_SERVICE_DEBUG=1

ENTRYPOINT gunicorn --bind "0.0.0.0:${PORT}" --log-level debug --workers 1 --worker-class entities_service.uvicorn.UvicornWorker --reload entities_service.main:APP

## PRODUCTION target
FROM base as production

ENV PORT=80
EXPOSE ${PORT}

# Force debug mode to be off, since we're running in production mode
ENV ENTITIES_SERVICE_DEBUG=0

ENTRYPOINT gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --worker-class entities_service.uvicorn.UvicornWorker entities_service.main:APP
