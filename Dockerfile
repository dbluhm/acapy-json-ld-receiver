FROM python:3.9-slim-bookworm AS base
WORKDIR /usr/src/app

# Install and configure poetry
ENV POETRY_VERSION="1.7.1"
ENV POETRY_HOME=/opt/poetry
RUN apt-get update && apt-get install -y curl && apt-get clean
RUN curl -sSL https://install.python-poetry.org | python -

ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Setup project
RUN mkdir src && touch src/__init__.py
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-dev -E server

FROM python:3.9-slim-bookworm
LABEL healthcheck="nc -z 127.0.0.1 80"
WORKDIR /usr/src/app
COPY --from=base /usr/src//app/.venv /usr/src//app/.venv
ENV PATH="/usr/src//app/.venv/bin:$PATH"
RUN apt-get update && apt-get install -y netcat-traditional && apt-get clean
EXPOSE 80

COPY src src
ENTRYPOINT ["uvicorn", "src:app"]
CMD ["--host", "0.0.0.0", "--port", "80"]
