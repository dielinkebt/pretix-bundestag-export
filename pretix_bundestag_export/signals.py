"""
Signal-Registrierung für den Exporter.

pretix nutzt zwei verschiedene Signale für Exporter:

1. register_data_exporters
   → Exporter erscheint unter Veranstaltung → Bestellungen → Export
   → Wird pro Event aufgerufen (sender = Event)

2. register_multievent_data_exporters
   → Exporter erscheint auf Organizer-Ebene für mehrere Events gleichzeitig
   → Optional, falls veranstaltungsübergreifender Export gewünscht

Laut pretix-Dokumentation müssen beide Signale registriert werden,
wenn der Exporter sowohl auf Event- als auch auf Organizer-Ebene
verfügbar sein soll.
"""

from django.dispatch import receiver
from pretix.base.signals import register_data_exporters


# Signal 1: Event-Ebene
# Der Exporter erscheint unter Veranstaltung → Bestellungen → Export,
# sobald das Plugin für diese Veranstaltung aktiviert ist.
@receiver(register_data_exporters, dispatch_uid="pretix_bundestag_exporter_event")
def register_exporter(sender, **kwargs):
    """
    Registriert den Exporter für event-spezifische Exporte.
    sender ist hier die jeweilige Event-Instanz.
    """
    from .exporter import BundestagDataExporter
    return BundestagDataExporter