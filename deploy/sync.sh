#!/bin/bash
# Rsync repo ke VM Satu Data Banten (tanpa .env — file secret tetap di server).
#
# Usage:
#   ./deploy/sync.sh dev          # → ssh-banten-dev (10.255.100.246)
#   ./deploy/sync.sh prod         # → ssh-banten-prod (10.249.100.25)
#   ./deploy/sync.sh prod --dry-run
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"
DRY_RUN=""

if [[ "${2:-}" == "--dry-run" ]]; then
  DRY_RUN="--dry-run"
fi

case "${TARGET}" in
  dev|development|vm-banten|ssh-banten-dev)
    SSH_HOST="ssh-banten-dev"
  ;;
  prod|production|ssh-banten-prod)
    SSH_HOST="ssh-banten-prod"
  ;;
  *)
    echo "Usage: $0 {dev|prod} [--dry-run]" >&2
    echo "  dev  → ssh-banten-dev  (10.255.100.246)" >&2
    echo "  prod → ssh-banten-prod (10.249.100.25)" >&2
    exit 1
  ;;
esac

REMOTE="${SSH_HOST}:~/satudata/"

echo "Sync → ${REMOTE}"
echo "From: ${REPO_DIR}"

RSYNC_OPTS=(
  -avz
  --delete
  --exclude '.git/'
  --exclude '.env'
  --exclude '.env.*'
  --exclude 'migration/'
  --exclude 'vm-backup/'
  --exclude 'data/'
  --exclude '*.dump'
  --exclude '*.tar.gz'
  --exclude '__pycache__/'
  --exclude '.DS_Store'
  --exclude 'venv/'
  --exclude 'node_modules/'
)

if [[ -n "${DRY_RUN}" ]]; then
  RSYNC_OPTS+=(--dry-run)
fi

rsync "${RSYNC_OPTS[@]}" "${REPO_DIR}/" "${REMOTE}"

echo "Done. Next on VM: ssh ${SSH_HOST} 'cd ~/satudata && bash deploy/update.sh'"
