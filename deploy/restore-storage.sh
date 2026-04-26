#!/bin/bash
# Restore CKAN file storage (resources, dll) dari tarball
#
# Tarball harus berisi struktur: default/storage/...
# (matches /var/lib/ckan/default pada VM lama)
#
# Usage: bash deploy/restore-storage.sh /path/to/var-lib-ckan.tar.gz

set -e

TAR_FILE="${1:-}"
[[ -z "$TAR_FILE" || ! -f "$TAR_FILE" ]] && {
    echo "Usage: $0 /path/to/storage-tarball.tar.gz"
    exit 1
}

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
source .env

DATA_DIR="${DATA_DIR:-/var/lib/satudata-data}"
TARGET="$DATA_DIR/ckan_storage"

echo "================================================"
echo "Restore storage: $TAR_FILE"
echo "Target: $TARGET"
echo "================================================"

# Tar contents preview
echo ""
echo "Tarball top-level entries:"
tar -tzf "$TAR_FILE" 2>/dev/null | head -10
echo ""

read -p "Lanjut extract ke $TARGET? (y/N): " confirm
[[ "$confirm" != "y" && "$confirm" != "Y" ]] && { echo "Aborted."; exit 0; }

# Detect structure
FIRST_ENTRY=$(tar -tzf "$TAR_FILE" 2>/dev/null | head -1)
if [[ "$FIRST_ENTRY" == "default/"* ]]; then
    echo "Tar berisi 'default/...' — extract dengan strip 1 supaya match struktur."
    sudo tar xzf "$TAR_FILE" -C "$TARGET" --strip-components=1 2>/dev/null || true
elif [[ "$FIRST_ENTRY" == "storage/"* ]]; then
    echo "Tar berisi 'storage/...' — extract apa adanya."
    sudo tar xzf "$TAR_FILE" -C "$TARGET" 2>/dev/null || true
else
    echo "Unknown structure, extract apa adanya ke $TARGET."
    sudo tar xzf "$TAR_FILE" -C "$TARGET" 2>/dev/null || true
fi

# Fix ownership for ckan user (uid 92 in ckan-base image)
echo ""
echo "Fixing ownership (uid 92, gid 92 = ckan user)..."
sudo chown -R 92:92 "$TARGET"

echo ""
echo "Result:"
sudo du -sh "$TARGET"
sudo ls "$TARGET" | head -10

echo ""
echo "================================================"
echo "Storage restore done."
echo "================================================"
