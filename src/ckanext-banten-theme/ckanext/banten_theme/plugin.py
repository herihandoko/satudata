from datetime import datetime
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.banten_theme.views import (
    metrix as metrix_blueprint,
    dokumentasi as dokumentasi_blueprint,
)

log = logging.getLogger(__name__)


def banten_current_year():
    """Return the current year as a string (e.g. '2026')."""
    return str(datetime.now().year)


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

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'banten_theme')

    def get_helpers(self):
        return {
            'banten_current_year': banten_current_year,
            'banten_recent_datasets': banten_recent_datasets,
        }

    def get_blueprint(self):
        return [metrix_blueprint, dokumentasi_blueprint]
