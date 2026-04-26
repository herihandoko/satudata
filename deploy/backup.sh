#!/bin/bash
# Daily backup script — DB dump + storage tarball
# Bisa dijalankan via cron untuk automatic backup
#
# Cron example (jam 2 dini hari):
#   0 2 * * * /home/USER/satudata/deploy/backup.sh >> /var/log/satudata-backup.log 2>&1

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
source .env

BACKUP_ROOT="${BACKUP_DIR:-/var/lib/satudata-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"

echo "================================================"
echo "Satudata Backup — $TIMESTAMP"
echo "================================================"

# 1. Database
echo ""
echo "[1/3] Backing up database..."
docker compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U "$CKAN_DB_USER" -d "$CKAN_DB" \
    -Fc --no-owner --no-privileges \
    > "$BACKUP_DIR/ckan_default.dump"
ls -lh "$BACKUP_DIR/ckan_default.dump"

# 2. CKAN storage
echo ""
echo "[2/3] Backing up CKAN storage..."
DATA_DIR="${DATA_DIR:-/var/lib/satudata-data}"
sudo tar czf "$BACKUP_DIR/ckan_storage.tar.gz" -C "$DATA_DIR" ckan_storage 2>/dev/null
sudo chown $(id -u):$(id -g) "$BACKUP_DIR/ckan_storage.tar.gz"
ls -lh "$BACKUP_DIR/ckan_storage.tar.gz"

# 3. Metadata
echo ""
echo "[3/3] Saving metadata..."
cat > "$BACKUP_DIR/info.txt" <<META
Backup created: $(date)
Hostname: $(hostname)
Git commit: $(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null)
Containers:
$(docker compose -f docker-compose.prod.yml ps --format 'table {{.Name}}\t{{.Status}}')
META
cat "$BACKUP_DIR/info.txt"

# Cleanup old backups
echo ""
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_ROOT" -maxdepth 1 -type d -name '20*' -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
echo "Remaining backups:"
ls -1d "$BACKUP_ROOT"/20* 2>/dev/null | tail -10

echo ""
echo "================================================"
echo "Backup done: $BACKUP_DIR"
du -sh "$BACKUP_DIR"
echo "================================================"
