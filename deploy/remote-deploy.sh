#!/usr/bin/env bash
# Runs ON the app host (as root, via SSM Run Command) with the unpacked release
# directory as $1. Swaps it into /opt/app, writes .env from SSM Parameter Store
# and restarts the stack. Never run on a laptop.
set -euo pipefail

RELEASE_DIR="${1:?usage: remote-deploy.sh <release-dir>}"
APP_DIR=/opt/app
ENV_PARAMETER="${ENV_PARAMETER:-/aicsp/prod/env}"

umask 077
aws ssm get-parameter --name "$ENV_PARAMETER" --with-decryption \
  --query Parameter.Value --output text > "$RELEASE_DIR/.env"

mkdir -p "$APP_DIR"
find "$APP_DIR" -mindepth 1 -delete
cp -a "$RELEASE_DIR"/. "$APP_DIR"/
chown -R ec2-user:ec2-user "$APP_DIR"
chmod 600 "$APP_DIR/.env"

cd "$APP_DIR"
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
docker compose -f docker-compose.prod.yml ps
docker image prune -f >/dev/null
