#!/bin/sh

set -e

# Configure CKAN locale from env vars on every container start.
# This works in both dev and prod images because docker-entrypoint.d
# scripts are always copied and executed.
CKAN_LOCALE_DEFAULT="${CKAN__LOCALE_DEFAULT:-id}"
CKAN_LOCALES_OFFERED="${CKAN__LOCALES_OFFERED:-en id}"

echo "Setting CKAN locale: default=${CKAN_LOCALE_DEFAULT}, offered=${CKAN_LOCALES_OFFERED}"
ckan config-tool "$CKAN_INI" \
  "ckan.locale_default = ${CKAN_LOCALE_DEFAULT}" \
  "ckan.locales_offered = ${CKAN_LOCALES_OFFERED}"
