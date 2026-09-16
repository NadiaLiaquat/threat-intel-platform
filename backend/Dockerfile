FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

# Used for both the api and collector services — docker-compose.yml picks
# the entrypoint per service via `command:`.
