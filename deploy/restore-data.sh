#!/bin/bash
# Restore PostgreSQL data dari dump file (format custom -Fc)
#
# Usage:  bash deploy/restore-data.sh /path/to/ckan_default.dump
#
# Catatan:
# - Akan menghapus data CKAN yang sudah ada di container db (--clean)
# - Solr index harus di-rebuild setelah restore: ckan search-index rebuild

set -e

DUMP_FILE="${1:-}"
[[ -z "$DUMP_FILE" || ! -f "$DUMP_FILE" ]] && {
    echo "Usage: $0 /path/to/dump-file.dump"
    exit 1
}

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
source .env

echo "================================================"
echo "Restore database: $DUMP_FILE"
echo "Target: $CKAN_DB_USER@db/$CKAN_DB"
echo "================================================"
read -p "Lanjut? Ini akan OVERWRITE data CKAN yang ada di container. (y/N): " confirm
[[ "$confirm" != "y" && "$confirm" != "Y" ]] && { echo "Aborted."; exit 0; }

# Pre-restore backup (safety)
echo ""
echo "Pre-restore backup..."
SAFETY_BACKUP="$HOME/satudata-pre-restore-$(date +%Y%m%d_%H%M%S).dump"
docker compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U "$CKAN_DB_USER" -d "$CKAN_DB" -Fc --no-owner --no-privileges \
    > "$SAFETY_BACKUP" 2>/dev/null || echo "  (DB mungkin kosong, skip)"
[[ -f "$SAFETY_BACKUP" ]] && ls -lh "$SAFETY_BACKUP"

# Copy dump ke container & restore
echo ""
echo "Copying dump into db container..."
docker compose -f docker-compose.prod.yml cp "$DUMP_FILE" db:/tmp/restore.dump

echo ""
echo "Running pg_restore (this may take a while)..."
docker compose -f docker-compose.prod.yml exec -T db pg_restore \
    -U "$CKAN_DB_USER" -d "$CKAN_DB" \
    --clean --if-exists --no-owner --no-privileges \
    /tmp/restore.dump 2>&1 | tail -20 || echo "(some warnings are normal)"

# Cleanup
docker compose -f docker-compose.prod.yml exec -T db rm -f /tmp/restore.dump

echo ""
echo "Running CKAN db upgrade (apply migrations)..."
docker compose -f docker-compose.prod.yml exec -T ckan ckan db upgrade || echo "(may fail if already up-to-date)"

echo ""
echo "================================================"
echo "Database restore done."
echo ""
echo "Don't forget to rebuild Solr index:"
echo "  docker compose -f docker-compose.prod.yml exec ckan ckan search-index rebuild"
echo ""
echo "Pre-restore safety backup: $SAFETY_BACKUP"
echo "================================================"
