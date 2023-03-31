FROM python:3.10-slim as base

WORKDIR /app

COPY dlite_entities_service dlite_entities_service/
COPY pyproject.toml LICENSE README.md ./

RUN python -m pip install -U pip && \
  pip install -U pip setuptools wheel flit && \
  pip install -U uvicorn && \
  pip install -U -e .

EXPOSE 80

FROM base as development

ENTRYPOINT uvicorn --host 0.0.0.0 --port 80 --log-level debug --no-server-header --header "Server:DLiteEntitiesService" --reload dlite_entities_service.main:APP

FROM base as production

ENTRYPOINT uvicorn --host 0.0.0.0 --port 80 --no-server-header --header "Server:DLiteEntitiesService" dlite_entities_service.main:APP
