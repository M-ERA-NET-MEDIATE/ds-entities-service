FROM python:3.10-slim as base

WORKDIR /app

COPY entities_service entities_service/
COPY pyproject.toml LICENSE README.md ./

# Install dependencies
RUN python -m pip install -U pip && \
  pip install -U pip setuptools wheel flit && \
  pip install -U uvicorn && \
  pip install -U -e . && \
  # Create log directory and file (if not existing already)
  mkdir -p logs && \
  touch -a logs/entities_service.log

FROM base as development

ENV PORT=80
EXPOSE ${PORT}

ENTRYPOINT uvicorn --host 0.0.0.0 --port ${PORT} --log-level debug --no-server-header --header "Server:EntitiesService" --reload entities_service.main:APP

FROM base as production

RUN pip install gunicorn

ENV PORT=80
EXPOSE ${PORT}

ENTRYPOINT gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --worker-class entities_service.uvicorn.UvicornWorker entities_service.main:APP
