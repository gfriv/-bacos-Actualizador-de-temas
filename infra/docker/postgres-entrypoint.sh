#!/bin/sh
set -eu

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-$POSTGRES_USER}"

ensure_database() {
  if [ "$POSTGRES_DB" = "postgres" ]; then
    return 0
  fi
  rm -f "$PGDATA/postmaster.pid"
  su-exec postgres pg_ctl -D "$PGDATA" -o "-c listen_addresses=''" -w start
  if ! su-exec postgres psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1; then
    su-exec postgres createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" "$POSTGRES_DB"
  fi
  su-exec postgres pg_ctl -D "$PGDATA" -m fast -w stop
}

mkdir -p "$PGDATA" /run/postgresql
chown -R postgres:postgres "$PGDATA" /run/postgresql
chmod 700 "$PGDATA"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  pwfile="$(mktemp)"
  printf '%s\n' "$POSTGRES_PASSWORD" > "$pwfile"
  chown postgres:postgres "$pwfile"
  chmod 600 "$pwfile"

  su-exec postgres initdb -D "$PGDATA" --username="$POSTGRES_USER" --pwfile="$pwfile" --auth-host=scram-sha-256 --auth-local=trust
  rm -f "$pwfile"

  {
    echo "listen_addresses = '*'"
    echo "password_encryption = 'scram-sha-256'"
  } >> "$PGDATA/postgresql.conf"
  {
    echo "local all all trust"
    echo "host all all 0.0.0.0/0 scram-sha-256"
    echo "host all all ::/0 scram-sha-256"
  } >> "$PGDATA/pg_hba.conf"

fi

ensure_database

exec su-exec postgres postgres -D "$PGDATA"
