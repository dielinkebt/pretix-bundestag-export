"""
pretix_bundestag_export
~~~~~~~~~~~~~~~~~~~~~~~
CSV- und Excel-Export von Teilnehmerdaten für Bundestagsveranstaltungen.
"""

from .apps import PretixBundestagExportApp

default_app_config = 'pretix_bundestag_export.apps.PretixBundestagExportApp'

__version__ = '0.1.0'
