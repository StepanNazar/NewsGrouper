FROM python:3.12-slim AS builder

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

COPY requirements.txt requirements.txt
RUN pip wheel --wheel-dir=/app/wheels -r requirements.txt



FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /sbin/nologin appuser

RUN --mount=type=bind,from=builder,source=/app/wheels,target=/tmp/wheels \
    pip install --no-index --find-links=/tmp/wheels /tmp/wheels/*
COPY --chown=appuser:appuser src/news_grouper/api news_grouper/api

USER appuser

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "news_grouper.api.prod:app"]