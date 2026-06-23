from flask import Blueprint
import ckan.plugins.toolkit as toolkit

from ckanext.banten_theme.metabase_embed import build_metrix_dashboard_url


metrix = Blueprint('metrix', __name__)
dokumentasi = Blueprint('dokumentasi', __name__)


@metrix.route('/metrix')
def index():
    """Metrix dashboard — Metabase signed embed (or public fallback).

    iframe src is a same-origin path (/metrix-dashboard/...) proxied by nginx
    to Metabase so browsers never call the private IP directly.
    """
    return toolkit.render('metrix.html', extra_vars={
        'dashboard_url': build_metrix_dashboard_url(),
        'page_title': 'Metrix',
    })


@dokumentasi.route('/dokumentasi')
def index():
    """Static documentation page for data consumers (download / API)."""
    return toolkit.render('dokumentasi.html', extra_vars={
        'page_title': 'Dokumentasi',
    })
