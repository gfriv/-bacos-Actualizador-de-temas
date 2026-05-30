#!/bin/sh
set -eu

cd /app/apps/api
alembic upgrade head
exec "$@"
