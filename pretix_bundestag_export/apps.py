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
    # Muss exakt dem Python-Paketnamen entsprechen.
    name = 'pretix_bundestag_export'
    verbose_name = _('Datenexport (Bundestag)')

    class PretixPluginMeta:
        name = _('Datenexport (Bundestag)')
        author = 'Die Linke im Bundestag'
        version = '0.1.1'
        # CUSTOMIZATION ist die Standard-Kategorie für Plugins ohne eigene Kategorie.
        # Damit erscheint das Plugin im richtigen Abschnitt der Plugin-Liste.
        category = 'FORMAT'
        # PLUGIN_LEVEL_ORGANIZER: Plugin wird auf Veranstalter-Ebene aktiviert
        # und gilt dann automatisch für alle Veranstaltungen dieses Organizers.
        level = PLUGIN_LEVEL_ORGANIZER
        visible = True
        description = _(
            'Exportiert Teilnehmerdaten einer Veranstaltung als CSV oder Excel '
            'mit Name, Vorname(n) und Geburtsdatum zur Anmeldung im Bundestag.'
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
