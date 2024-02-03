FROM python:3.7-slim-bullseye AS base
WORKDIR /app

# Install and configure poetry
ENV POETRY_VERSION=1.1.11
ENV POETRY_HOME=/opt/poetry
RUN apt update && apt install -y curl && apt clean
RUN curl -sSL https://install.python-poetry.org | python -

ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Setup project
RUN mkdir src && touch src/__init__.py
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-dev -E server

FROM python:3.7-slim-bullseye
LABEL healthcheck="nc -z 127.0.0.1 80"
WORKDIR /app
COPY --from=base /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN apt update && apt install -y netcat && apt clean
EXPOSE 80

COPY src src
ENTRYPOINT ["uvicorn", "src:app"]
CMD ["--host", "0.0.0.0", "--port", "80"]
