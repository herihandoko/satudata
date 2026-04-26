from datetime import datetime

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def banten_current_year():
    """Return the current year as a string (e.g. '2026')."""
    return str(datetime.now().year)


class BantenThemePlugin(plugins.SingletonPlugin):
    """SATU DATA Banten — Provincial open-data portal theme.

    Provides a gov-formal visual identity using Banten provincial colors
    (primary green #0f8d44) and the Banten provincial logo.
    """

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    def get_helpers(self):
        return {
            'banten_current_year': banten_current_year,
        }
