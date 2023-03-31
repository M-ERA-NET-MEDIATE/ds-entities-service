FROM python:3.10-slim as base

WORKDIR /app

COPY dlite_entities_service dlite_entities_service/
COPY pyproject.toml LICENSE README.md ./

RUN python -m pip install -U pip && \
  pip install -U pip setuptools wheel flit && \
  pip install -U uvicorn && \
  pip install -U -e .

FROM base as development

ENV PORT=80
EXPOSE ${PORT}

ENTRYPOINT uvicorn --host 0.0.0.0 --port ${PORT} --log-level debug --no-server-header --header "Server:DLiteEntitiesService" --reload dlite_entities_service.main:APP

FROM base as production

RUN pip install gunicorn

ENV PORT=80
EXPOSE ${PORT}

ENTRYPOINT gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --worker-class dlite_entities_service.uvicorn.UvicornWorker dlite_entities_service.main:APP
