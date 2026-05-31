FROM alpine:3.20

WORKDIR /app

RUN apk add --no-cache python3 py3-pip libstdc++ && ln -sf python3 /usr/bin/python
COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/
RUN python -m pip install --no-cache-dir --break-system-packages uv && cd apps/api && uv sync --frozen --no-dev

COPY apps/api apps/api
COPY workers workers
COPY infra/docker/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh
RUN chmod +x /usr/local/bin/api-entrypoint.sh

ENV PATH="/app/apps/api/.venv/bin:$PATH"
ENV PYTHONPATH="/app/apps/api:/app"
WORKDIR /app/apps/api

ENTRYPOINT ["api-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
