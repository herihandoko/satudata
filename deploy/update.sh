#!/bin/bash
# Update script — sync source code dari git, rebuild & restart container
# DATA TIDAK TERSENTUH (postgres, solr, ckan_storage tetap aman di $DATA_DIR)
#
# Usage:  bash deploy/update.sh
# Run as: user yang sama dengan yang `docker compose up -d`

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "================================================"
echo "Satudata Update"
echo "$(date)"
echo "================================================"

# 1. Pre-update DB backup (safety net)
echo ""
echo "[1/5] Quick DB backup before update..."
BACKUP_DIR="$HOME/satudata-update-backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/pre-update-${TIMESTAMP}.dump"
docker compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U "${CKAN_DB_USER:-ckandbuser}" \
    -d "${CKAN_DB:-ckandb}" \
    -Fc --no-owner --no-privileges \
    > "$BACKUP_FILE" 2>/dev/null || echo "  WARN: backup failed, continuing"
ls -lh "$BACKUP_FILE" 2>/dev/null
# Keep last 10 backups
ls -1t "$BACKUP_DIR"/pre-update-*.dump 2>/dev/null | tail -n +11 | xargs -r rm -f

# 2. Pull latest source from git
echo ""
echo "[2/5] Pulling latest source from git..."
git fetch origin
echo "Current: $(git log -1 --oneline)"
echo "Remote:  $(git log -1 --oneline origin/master 2>/dev/null || git log -1 --oneline origin/main 2>/dev/null)"
git pull --ff-only

# 3. Rebuild image (only if Dockerfile or src/ changed)
echo ""
echo "[3/5] Rebuilding CKAN image..."
docker compose -f docker-compose.prod.yml build ckan

# 4. Restart with zero-downtime where possible
echo ""
echo "[4/5] Recreating CKAN container..."
docker compose -f docker-compose.prod.yml up -d --no-deps ckan datapusher

# 5. Wait & verify
echo ""
echo "[5/5] Verifying..."
sleep 15
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Health check:"
curl -fsS http://127.0.0.1:${CKAN_PORT_HOST:-8080}/api/action/status_show | head -c 200 || echo "  WARN: CKAN not responding yet, check logs"
echo ""

echo ""
echo "================================================"
echo "Update done. Pre-update backup: $BACKUP_FILE"
echo "Logs:  docker compose -f docker-compose.prod.yml logs -f ckan --tail=100"
echo "================================================"
