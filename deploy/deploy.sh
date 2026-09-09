#!/usr/bin/env bash
# Sync the working tree to the app host and (re)start the production stack.
#
#   deploy/deploy.sh
#
# Reads the host IP from terraform output. Expects deploy/.env.prod to exist
# locally (created from deploy/.env.prod.example) -- it is copied to the host
# as .env and never committed.
set -euo pipefail

cd "$(dirname "$0")/.."

SSH_KEY="${SSH_KEY:-$HOME/.ssh/aicsp}"
REMOTE_DIR="/opt/app"

IP="$(terraform -chdir=deploy/terraform output -raw app_ip)"
HOST="ec2-user@${IP}"
SSH="ssh -i ${SSH_KEY} -o StrictHostKeyChecking=accept-new ${HOST}"

echo "==> Deploying to ${HOST}"

test -f deploy/.env.prod || { echo "missing deploy/.env.prod (copy from deploy/.env.prod.example)"; exit 1; }

# Ship the code (skip local build artefacts and secrets).
rsync -az --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'frontend/dist' \
  --exclude 'backend/.venv' \
  --exclude 'backend/chroma_db' \
  --exclude 'backend/uploads' \
  --exclude '*.db' \
  --exclude '.env' \
  --exclude 'deploy/.env.prod' \
  -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=accept-new" \
  ./ "${HOST}:${REMOTE_DIR}/"

scp -i "${SSH_KEY}" deploy/.env.prod "${HOST}:${REMOTE_DIR}/.env"

# shellcheck disable=SC2087
$SSH bash -s <<'REMOTE'
set -euo pipefail
cd /opt/app
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
REMOTE

echo
echo "==> Done. https://$(terraform -chdir=deploy/terraform output -raw site_address)"
