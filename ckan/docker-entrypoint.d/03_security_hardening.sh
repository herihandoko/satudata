#!/bin/sh
# Apply security hardening to ckan.ini on every container start.
#
# Implements quick-win fixes from pentest report (28-29 April 2026):
#   HIGH-1  Disable anonymous user_list / user_show enumeration
#   MEDIUM-2 Cookie remember_token: SameSite=Lax + Secure (HTTPS only)
#   LOW-1   Default API token expiry 90 days
#
# Cookie Secure flags are auto-enabled only when CKAN_SITE_URL starts with
# https:// so local development over HTTP keeps working.

set -e

apply() {
  ckan config-tool "$CKAN_INI" "$@"
}

echo "Applying security hardening (auth + token + cookies)..."

# HIGH-1 + MEDIUM-1 (email_hash exposure auto-fixed once user_list is private)
apply \
  "ckan.auth.public_user_details = false" \
  "ckan.auth.public_activity_stream_detail = false"

# LOW-1
apply \
  "ckan.api_token.expires_in.default = 7776000"

# MEDIUM-2 — Flask / Flask-Login cookie hardening
SECURE_FLAG="false"
case "${CKAN_SITE_URL}" in
  https://*) SECURE_FLAG="true" ;;
esac

apply \
  "SESSION_COOKIE_HTTPONLY = true" \
  "SESSION_COOKIE_SAMESITE = Lax" \
  "SESSION_COOKIE_SECURE = ${SECURE_FLAG}" \
  "REMEMBER_COOKIE_HTTPONLY = true" \
  "REMEMBER_COOKIE_SAMESITE = Lax" \
  "REMEMBER_COOKIE_SECURE = ${SECURE_FLAG}" \
  "WTF_CSRF_SSL_STRICT = ${SECURE_FLAG}"

echo "Security hardening applied (SECURE cookies=${SECURE_FLAG})."
