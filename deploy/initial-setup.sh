#!/bin/bash
# Initial deployment setup for VM (run ONCE on first deploy)
#
# Usage: bash deploy/initial-setup.sh
#
# Pre-requirements:
#   - Docker & Docker Compose installed
#   - Sudo access on VM
#   - Repo sudah di-clone di /home/$USER/satudata
#   - File .env sudah di-copy & di-edit dari .env.production.example

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${DATA_DIR:-/var/lib/satudata-data}"

echo "================================================"
echo "Satudata Initial VM Setup"
echo "Repo: $REPO_DIR"
echo "Data: $DATA_DIR"
echo "================================================"

# 1. Validate prerequisites
echo ""
echo "[1/6] Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not installed"; exit 1; }
command -v docker compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || { echo "ERROR: docker compose plugin not available"; exit 1; }
[[ -f "$REPO_DIR/.env" ]] || { echo "ERROR: $REPO_DIR/.env not found. Copy from .env.production.example first."; exit 1; }
echo "OK"

# 2. Validate .env has been customized
echo ""
echo "[2/6] Checking .env for unset secrets..."
if grep -q "CHANGE_ME" "$REPO_DIR/.env"; then
    echo "ERROR: .env masih ada placeholder CHANGE_ME. Edit dulu."
    grep -n "CHANGE_ME" "$REPO_DIR/.env" | head -5
    exit 1
fi
echo "OK"

# 3. Create data directories
echo ""
echo "[3/6] Creating data directories at $DATA_DIR..."
sudo mkdir -p "$DATA_DIR"/{postgres,solr,ckan_storage,redis}
sudo chown -R 999:999 "$DATA_DIR/postgres"      # postgres user in container
sudo chown -R 8983:8983 "$DATA_DIR/solr"        # solr user in container
sudo chown -R 92:92 "$DATA_DIR/ckan_storage"    # ckan user (ckan-base image)
sudo chown -R 999:1000 "$DATA_DIR/redis"        # redis user
ls -la "$DATA_DIR"
echo "OK"

# 4. Build images
echo ""
echo "[4/6] Building Docker images..."
cd "$REPO_DIR"
docker compose -f docker-compose.prod.yml build
echo "OK"

# 5. Start services (db & solr first to init)
echo ""
echo "[5/6] Starting infrastructure (db, solr, redis)..."
docker compose -f docker-compose.prod.yml up -d db solr redis
echo "Waiting 30s for services to become healthy..."
sleep 30
docker compose -f docker-compose.prod.yml ps

# 6. Start CKAN
echo ""
echo "[6/6] Starting CKAN..."
docker compose -f docker-compose.prod.yml up -d
echo ""
echo "Waiting 60s for CKAN initialization..."
sleep 60

echo ""
echo "================================================"
echo "Setup complete!"
echo "================================================"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Logs CKAN: docker compose -f docker-compose.prod.yml logs -f ckan"
echo "Test:      curl http://127.0.0.1:8080/api/action/status_show"
echo ""
echo "Next steps:"
echo "  1. Restore database:    bash deploy/restore-data.sh /path/to/ckan_default.dump"
echo "  2. Restore storage:     bash deploy/restore-storage.sh /path/to/var-lib-ckan.tar.gz"
echo "  3. Configure nginx:     edit /etc/nginx/sites-available/* to proxy_pass to 127.0.0.1:8080"
echo "  4. Rebuild Solr index:  docker compose -f docker-compose.prod.yml exec ckan ckan search-index rebuild"
