#!/bin/bash
# Setup ckan.datapusher.api_token using the configured sysadmin user.
# Skips if CKAN__DATAPUSHER__API_TOKEN env var is set (manual override),
# or if the api_token already has a real value (idempotent across restarts).

# This script is sourced by start scripts (`. "$f"`), so plain `exit` would
# terminate the parent process. Use safe_exit to return when sourced.
safe_exit() {
    code="${1:-0}"
    return "$code" 2>/dev/null || exit "$code"
}

if [[ $CKAN__PLUGINS != *"datapusher"* ]]; then
    echo "Not configuring DataPusher (plugin not enabled)"
    safe_exit 0
fi

# Env var override: respect manually-provided token
if [ -n "$CKAN__DATAPUSHER__API_TOKEN" ]; then
    echo "Using CKAN__DATAPUSHER__API_TOKEN from environment"
    ckan config-tool "$CKAN_INI" "ckan.datapusher.api_token=$CKAN__DATAPUSHER__API_TOKEN"
    safe_exit 0
fi

# Idempotent: if a real token (>10 chars, not the 'xxx' placeholder set
# by start_ckan.sh) is already in ckan.ini, leave it alone.
EXISTING=$(grep -E "^ckan.datapusher.api_token=" "$CKAN_INI" | cut -d= -f2-)
if [ -n "$EXISTING" ] && [ "$EXISTING" != "xxx" ] && [ ${#EXISTING} -gt 10 ]; then
    echo "ckan.datapusher.api_token already configured, skipping"
    safe_exit 0
fi

# Determine sysadmin user to attach token to. Default to CKAN_SYSADMIN_NAME
# (the user that prerun.py creates), fall back to 'admin' or 'ckan_admin'.
SYSADMIN="${CKAN_SYSADMIN_NAME:-admin}"

echo "Generating ckan.datapusher.api_token for user '$SYSADMIN'"
TOKEN=$(ckan -c "$CKAN_INI" user token add "$SYSADMIN" datapusher 2>/dev/null | tail -n 1 | tr -d '\t \r\n')

if [ -z "$TOKEN" ]; then
    echo "WARNING: failed to generate token for '$SYSADMIN' — DataPusher will not work" >&2
    # Leave existing 'xxx' placeholder so CKAN can at least boot
    safe_exit 0
fi

ckan config-tool "$CKAN_INI" "ckan.datapusher.api_token=$TOKEN"
echo "ckan.datapusher.api_token configured successfully"
