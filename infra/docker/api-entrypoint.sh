#!/bin/sh
set -eu

cd /app/apps/api
if [ "${RUN_ALEMBIC_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade head
fi
exec "$@"
