FROM python:3.13.11-slim

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV UV_COMPILE_BYTE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY ./pyproject.toml ./uv.lock ./.python-version /app/

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project --no-dev

COPY ./src /app/src
# for seeding
COPY ./seed.py /app/seed.py
# for migration
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

# Create non-root user and transfer ownership
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
  && chown -R appuser:appgroup /app

USER appuser

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.app:app --host 0.0.0.0 --port ${PORT:-9000} --reload"]
