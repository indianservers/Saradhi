FROM python:3.12-slim AS wheels
WORKDIR /build
COPY requirements-prod.lock ./
RUN python -m pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements-prod.lock

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app
WORKDIR /app
RUN groupadd --system --gid 10001 quickbuddy \
    && useradd --system --uid 10001 --gid quickbuddy --home-dir /nonexistent \
       --shell /usr/sbin/nologin quickbuddy
COPY --from=wheels /wheels /wheels
COPY requirements-prod.lock ./
RUN python -m pip install --no-index --find-links=/wheels -r requirements-prod.lock \
    && rm -rf /wheels requirements-prod.lock
COPY --chown=quickbuddy:quickbuddy backend ./backend
COPY --chown=quickbuddy:quickbuddy ai_platform ./ai_platform
USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=20s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]
CMD ["uvicorn", "backend.api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--timeout-graceful-shutdown", "20"]
