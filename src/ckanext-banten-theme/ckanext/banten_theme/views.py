from flask import Blueprint
import ckan.plugins.toolkit as toolkit


metrix = Blueprint('metrix', __name__)


@metrix.route('/metrix')
def index():
    """Metrix dashboard — embedded Metabase public dashboard.

    The iframe src points to a path served by the host nginx as a reverse
    proxy to the Metabase server (so the embedded content is delivered via
    HTTPS and is same-origin, avoiding mixed-content blocks).
    """
    return toolkit.render('metrix.html', extra_vars={
        'dashboard_url': '/metrix-dashboard/public/dashboard/'
                         '074806cf-11d0-481b-8714-c78d9856621d',
        'page_title': 'Metrix',
    })
