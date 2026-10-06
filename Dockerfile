FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-install-project --no-dev

COPY . .

RUN uv sync --frozen --no-cache --no-dev

EXPOSE 8001

# CMD ["/app/.venv/bin/fastapi", "run", "/app/src/orders_svc/main.py"]
CMD ["uv", "run", "fastapi", "dev", "/app/src/orders_svc/main.py", "--host", "0.0.0.0"]