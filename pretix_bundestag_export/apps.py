"""
App-Konfiguration für das pretix-Plugin „Datenexport (Bundestag)".
"""

try:
    from pretix.base.plugins import PluginConfig, PLUGIN_LEVEL_ORGANIZER
except ImportError:
    raise RuntimeError("Bitte pretix 2026.1.0 oder neuer verwenden.")

from django.utils.translation import gettext_lazy as _

__all__ = ['PretixBundestagExportApp']


class PretixBundestagExportApp(PluginConfig):
    name = 'pretix_bundestag_export'
    verbose_name = _('Exportiert eine Teilnehmendenliste zur Anmeldung von Gästen im Bundestag')

    class PretixPluginMeta:
        name = _('Teilnehmendenliste (Bundestag)')
        author = 'Die Linke im Bundestag'
        version = '0.1.2'
        category = 'FORMAT'
        level = PLUGIN_LEVEL_ORGANIZER
        visible = True
        description = _(
            'Exportiert Teilnehmendendaten einer Veranstaltung als CSV oder Excel '
            'mit Name, Vorname(n) und Geburtsdatum zur Anmeldung von Gästen im Bundestag.'
        )
        compatibility = 'pretix>=2026.1.0'
        # Kein settings_links-Eintrag nötig, da der Exporter keinen
        # eigenen Einstellungsbereich hat.
        settings_links = []

    def ready(self):
        """
        Registriert Signal-Receiver beim App-Start.
        Das importiert signals.py, wodurch der Exporter bei pretix bekannt gemacht wird.
        """
        from . import signals
