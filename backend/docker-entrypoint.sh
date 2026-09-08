#!/usr/bin/env bash
set -euo pipefail

# The API container owns schema migrations; the worker waits for the schema to
# exist by the time it picks up a job.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Running database migrations..."
  python -m alembic upgrade head
fi

exec "$@"
