FROM python:3.12-slim AS builder

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/app/.venv/bin:$PATH"

RUN python -m venv /app/.venv

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip uninstall -y pip setuptools wheel

FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /sbin/nologin appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser src/news_grouper/api news_grouper/api

USER appuser

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "news_grouper.api.prod:app"]