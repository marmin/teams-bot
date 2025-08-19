# Dockerfile

FROM python:3.11-slim

ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TZ=Europe/Zurich


RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc git libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml /app/

#COPY poetry.lock /app/

RUN poetry install --no-interaction --no-ansi --no-root

COPY src /app/src

EXPOSE 3978
CMD ["poetry", "run", "python", "-m", "bot.app"]