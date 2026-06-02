"""
Exporter-Implementierung für "Datenexport (Bundestag)".

Diese Datei enthält die eigentliche Exportlogik. Sie:
- sammelt die relevanten Teilnehmerdaten aus Bestellpositionen,
- liest Antworten auf System- und Zusatzfragen,
- wendet die Sonderlogik für Ausweisdokument-Namen an,
- erzeugt CSV oder Excel (.xlsx).

Wichtige Annahmen:
- Der Export läuft auf Event-Ebene.
- Es werden primär positionsbezogene Daten exportiert.
- Das Geburtsdatum liegt in der Frage mit interner Referenz GEBURTSDATUM.
- Wenn ANDERER_NAME == Ja, werden NACHNAME_AUSWEISDOKUMENT und
  VORNAME_AUSWEISDOKUMENT genutzt.
"""

from collections import OrderedDict
from datetime import date, datetime
import csv
import io

from django import forms
from django.utils.translation import gettext_lazy as _

from openpyxl import Workbook

from pretix.base.exporter import BaseExporter
from pretix.base.models import OrderPosition, QuestionAnswer


class BundestagDataExporter(BaseExporter):
    """
    Exporter für Bundestagslisten als CSV oder Excel.

    pretix instanziiert diese Klasse für ein Event und ruft dann:
    - export_form_fields (Property, gibt Formularfelder zurück)
    - render(form_data) (erzeugt die Datei)
    auf.
    """

    # Eindeutiger interner Bezeichner, darf nur Kleinbuchstaben enthalten.
    # Pflichtfeld laut pretix-Dokumentation.
    identifier = 'bundestag_export'

    # Anzeigename im Export-Dialog von pretix.
    # Pflichtfeld laut pretix-Dokumentation.
    verbose_name = _('Anmeldung (Bundestag)')

    # Optionale Beschreibung für den Export-Dialog
    description = _(
        'Exportiert Name, Vorname(n) und Geburtsdatum aus Teilnehmerdaten '
        'als CSV oder Excel für die Anmeldung beim Bundestag.'
    )

    # Optionale Kategorie-Gruppierung im Export-Dialog
    # Kein lazy-translate nötig, da pretix hier einen einfachen String erwartet.
    category = 'Teilnehmerexporte'

    @property
    def export_form_fields(self):
        """
        Konfigurationsfelder für den pretix-Exportdialog.

        Laut pretix-Dokumentation soll diese Property ein OrderedDict
        zurückgeben, damit die Feldreihenfolge stabil bleibt.

        Wir bieten zwei Optionen an:
        1. Dateiformat: CSV oder XLSX
        2. Nur bezahlte Bestellungen exportieren: Ja/Nein
        """
        return OrderedDict([
            (
                'format',
                forms.ChoiceField(
                    label=_('Dateiformat'),
                    choices=(
                        ('csv', _('CSV-Datei')),
                        ('xlsx', _('Excel-Datei (.xlsx)')),
                    ),
                    initial='xlsx',
                    required=True,
                )
            ),
            (
                'paid_only',
                forms.BooleanField(
                    label=_('Nur bezahlte Bestellungen exportieren'),
                    required=False,
                    initial=True,
                )
            ),
        ])

    def _get_answers_by_reference(self, position):
        """
        Liest alle Antworten einer Bestellposition und mappt sie nach
        interner Referenz (question.identifier).

        Rückgabe: dict[str, str]
            Schlüssel: interne Referenz der Frage (z. B. 'GEBURTSDATUM')
            Wert: gespeicherte Antwort als String

        Warum diese Hilfsfunktion?
        pretix speichert Fragenantworten in QuestionAnswer-Objekten.
        Für unsere Exportlogik müssen wir schnell auf Antworten per
        interner Referenz zugreifen können.
        """
        result = {}

        answers = (
            QuestionAnswer.objects
            .filter(orderposition=position)
            .select_related('question')
        )

        for answer in answers:
            # Sicherheitscheck: Antwort ohne zugehörige Frage überspringen
            if not answer.question:
                continue

            identifier = answer.question.identifier
            if not identifier:
                continue

            # answer.answer enthält den gespeicherten Rohwert als String.
            result[identifier] = answer.answer

        return result

    def _is_truthy_yes(self, value):
        """
        Interpretiert verschiedene mögliche Ja-Werte robust als True.

        Hintergrund:
        Je nach Fragetyp und pretix-Version kann ein Ja/Nein-Wert als
        True, 'True', 'true', '1', 'yes', 'ja' oder 'on' gespeichert sein.
        """
        if value is True:
            return True
        if value is None:
            return False
        return str(value).strip().lower() in {'true', '1', 'yes', 'ja', 'on'}

    def _format_birthdate(self, value):
        """
        Formatiert einen Datumswert robust als 'TT.MM.JJJJ'.

        Unterstützte Eingaben:
        - datetime.date
        - datetime.datetime
        - ISO-String wie '2026-05-29'
        - bereits formatiertes deutsches Datum

        Wenn kein gültiges Datum erkannt wird, wird der Ursprungswert als
        String zurückgegeben, damit keine Information verloren geht.
        """
        if not value:
            return ''

        if isinstance(value, datetime):
            return value.strftime('%d.%m.%Y')

        if isinstance(value, date):
            return value.strftime('%d.%m.%Y')

        value_str = str(value).strip()

        # Bekannte Datumsformate probieren: ISO, Deutsch, ISO mit Uhrzeit
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%Y-%m-%dT%H:%M:%S'):
            try:
                parsed = datetime.strptime(value_str, fmt)
                return parsed.strftime('%d.%m.%Y')
            except ValueError:
                pass

        # Unbekanntes Format: Originalwert zurückgeben, damit nichts verloren geht.
        return value_str

    def _get_export_rows(self, paid_only=False):
        """
        Baut die eigentlichen Exportzeilen auf.

        Jede Zeile ist ein Dictionary mit den Spalten:
        - Name
        - Vorname(n)
        - Geburtsdatum TT.MM.JJJJ

        Logik:
        1. Vorname/Nachname kommen aus attendee_name_parts (JSONField, dict).
        2. Falls ANDERER_NAME == Ja, werden stattdessen die Werte aus
           NACHNAME_AUSWEISDOKUMENT und VORNAME_AUSWEISDOKUMENT genutzt.
        3. Das Geburtsdatum wird aus GEBURTSDATUM gelesen und formatiert.
        """
        positions = (
            OrderPosition.objects
            .filter(order__event=self.event)
            # WICHTIG: attendee_name_parts ist ein JSONField, kein ForeignKey!
            # Es darf NICHT in select_related stehen – das würde einen
            # FieldError auslösen. JSONFields werden direkt mit dem
            # Datensatz geladen und brauchen kein select_related.
            .select_related('order', 'item')
            .order_by('order__code', 'positionid')
        )

        # Optional nur bezahlte Bestellungen exportieren
        if paid_only:
            positions = positions.filter(order__status='p')

        rows = []

        for position in positions:
            answers = self._get_answers_by_reference(position)

            # Standardwerte aus dem Teilnehmernamen.
            # attendee_name_parts ist ein JSONField und liefert ein dict,
            # KEIN Objekt mit Attributen! Deshalb .get() statt Punkt-Notation.
            # Beispiel-Inhalt: {'given_name': 'Max', 'family_name': 'Mustermann'}
            name_parts = position.attendee_name_parts or {}
            first_name = name_parts.get('given_name', '') or ''
            last_name = name_parts.get('family_name', '') or ''

            # Sonderlogik: Wenn ANDERER_NAME == Ja, Ausweisdaten verwenden
            use_document_name = self._is_truthy_yes(answers.get('ANDERER_NAME'))

            if use_document_name:
                last_name = (answers.get('NACHNAME_AUSWEISDOKUMENT') or '').strip()
                first_name = (answers.get('VORNAME_AUSWEISDOKUMENT') or '').strip()

            birthdate = self._format_birthdate(answers.get('GEBURTSDATUM'))

            rows.append({
                'Name': last_name,
                'Vorname(n)': first_name,
                'Geburtsdatum TT.MM.JJJJ': birthdate,
            })

        return rows

    def _render_csv(self, rows):
        """
        Erzeugt den CSV-Inhalt als Bytes.

        Wir verwenden ein Semikolon als Trennzeichen, da das im deutschen
        Excel-Umfeld meist kompatibler ist als ein Komma.

        UTF-8 mit BOM (utf-8-sig) sorgt dafür, dass Excel die Datei
        ohne Zeichensatz-Probleme öffnen kann.
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['Name', 'Vorname(n)', 'Geburtsdatum TT.MM.JJJJ'],
            delimiter=';'
        )

        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        return output.getvalue().encode('utf-8-sig')

    def _render_xlsx(self, rows):
        """
        Erzeugt den Excel-Inhalt als .xlsx-Datei im Speicher.

        openpyxl schreibt die Arbeitsmappe in einen BytesIO-Puffer,
        der anschließend als Bytes zurückgegeben wird.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = 'Bundestag-Export'

        headers = ['Name', 'Vorname(n)', 'Geburtsdatum TT.MM.JJJJ']
        ws.append(headers)

        for row in rows:
            ws.append([
                row['Name'],
                row['Vorname(n)'],
                row['Geburtsdatum TT.MM.JJJJ'],
            ])

        # Sinnvolle Spaltenbreiten für bessere Lesbarkeit
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 20

        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()

    def render(self, form_data, output_file=None):
        """
        Rendert die Exportdatei.

        Laut pretix-Dokumentation muss render() ein Tuple zurückgeben:
            (dateiname: str, mime_type: str, inhalt: bytes)

        Optional kann output_file als Parameter akzeptiert werden.
        In diesem Fall wird der Inhalt in das übergebene File-Handle
        geschrieben und None als drittes Element zurückgegeben.

        Pflichtmethode laut pretix-Dokumentation.
        """
        fmt = form_data.get('format', 'xlsx')
        paid_only = bool(form_data.get('paid_only'))

        rows = self._get_export_rows(paid_only=paid_only)

        # Event-Slug als Dateiname-Prefix für eindeutige Benennung
        event_slug = self.event.slug if self.event else 'export'

        if fmt == 'csv':
            content = self._render_csv(rows)
            filename = f'{event_slug}-bundestag-export.csv'
            mimetype = 'text/csv'
        else:
            content = self._render_xlsx(rows)
            filename = f'{event_slug}-bundestag-export.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        if output_file is not None:
            output_file.write(content)
            return filename, mimetype, None

        return filename, mimetype, content
