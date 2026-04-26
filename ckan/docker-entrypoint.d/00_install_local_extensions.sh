#!/bin/bash
# Auto-install editable Python packages from /srv/app/src_extensions on every boot.
# Lets locally-developed extensions (mounted via docker-compose volume) be picked
# up by CKAN without having to rebuild the image.

set -e

EXT_DIR="${SRC_EXTENSIONS_DIR:-/srv/app/src_extensions}"

if [[ ! -d "$EXT_DIR" ]]; then
    exit 0
fi

for ext in "$EXT_DIR"/*; do
    if [[ ! -d "$ext" ]]; then
        continue
    fi
    if [[ -f "$ext/setup.py" ]] || [[ -f "$ext/pyproject.toml" ]]; then
        echo "[banten-theme bootstrap] Installing local extension: $(basename "$ext")"
        pip install -q -e "$ext" || echo "[banten-theme bootstrap] WARN: failed to install $(basename "$ext")"
    fi
done
