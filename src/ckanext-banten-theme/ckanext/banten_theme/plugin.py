from datetime import datetime
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.banten_theme.views import (
    metrix as metrix_blueprint,
    dokumentasi as dokumentasi_blueprint,
)
from ckanext.banten_theme import rate_limiter
from ckanext.banten_theme.validators import (
    safe_remote_url,
    assert_safe_url_or_raise,
)

log = logging.getLogger(__name__)

BANTEN_PORTAL_VERSION = '1.0.0'


def banten_portal_version():
    """Portal release version shown in the site footer."""
    return BANTEN_PORTAL_VERSION


def banten_current_year():
    """Return the current year as a string (e.g. '2026')."""
    return str(datetime.now().year)


def banten_site_url():
    """Public CKAN site URL from ckan.site_url (matches CKAN_SITE_URL in .env)."""
    return (toolkit.config.get('ckan.site_url') or '').rstrip('/')


def banten_api_action_url(action=''):
    """Base URL for CKAN Action API v3, e.g. .../api/3/action/package_search."""
    base = f'{banten_site_url()}/api/3/action'
    return f'{base}/{action}' if action else f'{base}/{{action}}'


def banten_recent_datasets(limit=4):
    """Return the most recently modified public datasets.

    Used by the homepage "Dataset Terbaru" row. Falls back to an empty list
    on error so the homepage never 500s.
    """
    try:
        result = toolkit.get_action('package_search')(
            {'ignore_auth': True},
            {
                'q': '*:*',
                'sort': 'metadata_modified desc',
                'rows': int(limit),
                'fq': '+state:active',
                'include_private': False,
            },
        )
        return result.get('results', [])
    except Exception as e:  # noqa: BLE001
        log.warning('banten_recent_datasets failed: %s', e)
        return []


class BantenThemePlugin(plugins.SingletonPlugin):
    """SATU DATA Banten — Provincial open-data portal theme.

    Provides a gov-formal visual identity using Banten provincial colors
    (primary green #0f8d44) and the Banten provincial logo.
    """

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IResourceController, inherit=True)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'banten_theme')

    def get_helpers(self):
        return {
            'banten_current_year': banten_current_year,
            'banten_portal_version': banten_portal_version,
            'banten_recent_datasets': banten_recent_datasets,
            'banten_site_url': banten_site_url,
            'banten_api_action_url': banten_api_action_url,
        }

    def get_blueprint(self):
        return [
            metrix_blueprint,
            dokumentasi_blueprint,
            rate_limiter.get_blueprint(),
        ]

    def get_validators(self):
        return {"banten_safe_remote_url": safe_remote_url}

    def before_resource_create(self, context, resource):
        assert_safe_url_or_raise(resource.get('url'))

    def before_resource_update(self, context, current, resource):
        new_url = resource.get('url')
        if new_url and new_url != (current or {}).get('url'):
            assert_safe_url_or_raise(new_url)
