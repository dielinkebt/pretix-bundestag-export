# Pretix-Datenexportformat zur Anmeldung von Veranstaltungsteilnehmer*innen beim Bundestag

Ein [pretix](https://github.com/pretix/pretix)-Plugin für den standardisierten Export von Teilnehmerdaten aus Veranstaltungen als CSV- oder Excel-Datei (`.xlsx`). Das Plugin ist für einen sehr konkreten Anwendungsfall gedacht: den Export einer Teilnehmendenliste in einem vom Bundestag vorgegebenen Format.

## Format

Das Plugin erzeugt aus einer pretix-Veranstaltung eine strukturierte Liste von Teilnehmenden mit genau den Feldern, die für den vorgesehenen Bundestags-Export benötigt werden. Die Ausgabe kann wahlweise als CSV-Datei oder als Excel-Datei (`.xlsx`) erfolgen.

Die exportierten Spalten sind:

| Spalte | Inhalt |
|--------|--------|
| Name | Nachname der teilnehmenden Person |
| Vorname(n) | Vorname bzw. Vornamen der teilnehmenden Person |
| Geburtsdatum TT.MM.JJJJ | Geburtsdatum im Format `dd.mm.YYYY` |

## Funktionsweise des Exporters

Das Plugin wird in pretix als eigener Exporter registriert. Technisch geschieht das über das Signal `register_data_exporters`; dadurch erscheint der Exporter im Export-Bereich einer Veranstaltung unter "Bestellungen" -> "Export" -> "Teilnehmerexporte" und kann dort wie andere pretix-Exporte ausgewählt werden.

Beim Ausführen des Exports durchläuft der Exporter die Bestellpositionen einer Veranstaltung und liest daraus die relevanten Teilnehmerdaten aus. Die Exportlogik kombiniert dabei Systemdaten von pretix, etwa den Teilnehmernamen, mit Antworten auf Fragen, die über ihre **internen Referenzen** identifiziert werden.

Der Exporter bietet zwei Ausgabeformate an:

- CSV-Datei
- Excel-Datei (`.xlsx`)

Zusätzlich kann optional festgelegt werden, dass nur bezahlte Bestellungen exportiert werden. Diese Art zusätzlicher Exportparameter ist in pretix ausdrücklich über Formularfelder des Exporters vorgesehen.

## Zuordnung der Spalten

Die Spalten werden im Normalfall wie folgt befüllt:

| Spalte | Datenquelle |
|--------|-------------|
| Name | Nachname Teilnehmer*in, aus den pretix-Systemdaten zum Teilnehmernamen |
| Vorname(n) | Vorname Teilnehmer*in, aus den pretix-Systemdaten zum Teilnehmernamen |
| Geburtsdatum TT.MM.JJJJ | Antwort auf die Frage mit interner Referenz `GEBURTSDATUM` |

Das Geburtsdatum wird im Export immer in das Format `dd.mm.YYYY` umgewandelt. Wenn pretix intern bereits ein Datum speichert oder ein ISO-Datumsformat wie `YYYY-MM-DD` vorliegt, wird dieses Format sauber konvertiert. Liegt stattdessen bereits ein korrekt formatiertes Datum als Text vor, wird dieser Wert übernommen.

## Sonderlogik: abweichender Name laut Ausweisdokument

Das Plugin enthält eine spezielle Umschaltlogik für den Fall, dass der im System erfasste Name nicht mit dem amtlichen Ausweisdokument übereinstimmt.

Wenn die Frage "Der Name in meinem amtlichen Ausweisdokument unterscheidet sich vom angegebenen Namen." mit der internen Referenz `ANDERER_NAME` existiert und mit **Ja** beantwortet wurde, werden die Spalten **Name** und **Vorname(n)** nicht aus dem normalen Teilnehmernamen befüllt, sondern aus zwei anderen Fragen:

| Spalte | Datenquelle bei `ANDERER_NAME = Ja` |
|--------|------------------------------------|
| Name | `NACHNAME_AUSWEISDOKUMENT` |
| Vorname(n) | `VORNAME_AUSWEISDOKUMENT` |

Die Logik ist also:

Damit der Export korrekt funktioniert, müssen die internen Referenzen exakt so geschrieben sein wie unten beschrieben.

## Erforderliche interne Referenzen

Die folgenden internen Referenzen müssen in pretix vorhanden sein, wenn die jeweilige Funktion genutzt werden soll:

| Interne Referenz | Typische Bedeutung | Pflicht? |
|------------------|--------------------|----------|
| `GEBURTSDATUM` | Geburtsdatum der teilnehmenden Person | Ja |
| `ANDERER_NAME` | Ja/Nein-Frage, ob der Name im Ausweisdokument abweicht | Nur für Sonderlogik |
| `NACHNAME_AUSWEISDOKUMENT` | Nachname laut Ausweisdokument | Nur wenn `ANDERER_NAME` genutzt wird |
| `VORNAME_AUSWEISDOKUMENT` | Vorname(n) laut Ausweisdokument | Nur wenn `ANDERER_NAME` genutzt wird |

### Wichtig zu den Referenzen

- Die internen Referenzen müssen **exakt** mit diesen Bezeichnern übereinstimmen.
- Groß- und Kleinschreibung ist relevant, wenn der Exporter im Code exakt auf diese Kennungen prüft.
- Es zählt die **interne Referenz** der Frage, nicht der sichtbare Fragetext.
- Der sichtbare Fragetitel darf frei formuliert sein, solange die interne Referenz korrekt gesetzt ist.

## Installation

### 1. Plugin in das pretix-System bringen

Das Repository kann lokal installiert oder in ein bestehendes Plugin-Setup eingebunden werden. Typischerweise geschieht das per `pip`.

#### Installation

```bash
pip install pretix-bundestag-export
```

#### Installation für Entwicklungsumgebung

```bash
git clone https://github.com/dielinkebt/pretix-bundestag-export.git
cd pretix-bundestag-export
pip install -e .
```

#### Installation in Docker-Umgebung

Dazu einfach die Zeilen 3-5 im `Dockerfile` einfügen:

```Dockerfile
FROM pretix/standalone:stable

USER root
RUN pip3 install pretix-bundestag-export && \
    rm -rf ~/.cache/pip

USER pretixuser
RUN cd /pretix/src && make production
```

### 2. pretix neu starten

Nach der Installation muss pretix neu gestartet werden, damit die Plugin-Metadaten geladen und die Exporter-Signale registriert werden. pretix lädt Plugins als reguläre Django-App und aktiviert zusätzliche Funktionen über deren App-Konfiguration und Signal-Registrierung.

### 3. Plugin aktivieren

Anschließend muss das Plugin in pretix für die gewünschte Veranstaltung bzw. den gewünschten Kontext aktiviert werden, damit der Exporter verfügbar ist.

## Verwendung im pretix-Backend

Nach erfolgreicher Installation und Aktivierung erscheint der Exporter im Export-Bereich der Veranstaltung. Dort kann das gewünschte Dateiformat ausgewählt werden, also CSV oder Excel, und bei Bedarf die Einschränkung auf bezahlte Bestellungen gesetzt werden.

Der Export erzeugt anschließend eine Datei mit einer Zeile pro exportierter Bestellposition bzw. teilnehmender Person.

## Typische Fehlerquellen

### Falsche oder fehlende interne Referenzen

Der häufigste Fehler ist, dass die Fragen zwar inhaltlich vorhanden sind, aber die interne Referenz nicht exakt stimmt. Schon kleine Abweichungen wie `Geburtsdatum`, `geburtsdatum` oder `GEB_DATUM` würden dazu führen, dass der Exporter die Daten nicht im erwarteten Feld findet.

### Falscher Fragetyp

Für `ANDERER_NAME` sollte eine echte Ja/Nein-Frage verwendet werden. Wenn stattdessen ein Freitextfeld oder eine Auswahl mit unerwarteten Werten genutzt wird, kann die Umschaltlogik unzuverlässig werden.

### Leere Ausweisdokument-Felder

Wenn `ANDERER_NAME` mit Ja beantwortet wird, aber `NACHNAME_AUSWEISDOKUMENT` oder `VORNAME_AUSWEISDOKUMENT` leer bleiben, dann werden entsprechend leere Werte exportiert. Die Validierung dieser Eingaben sollte daher möglichst schon im pretix-Formular sichergestellt werden.

### Abweichende Namenskonfiguration in pretix

Das Plugin nutzt für den Standardfall die Teilnehmer-Namensdaten aus dem pretix-System. Wenn eine Instanz oder ein Event sehr speziell konfiguriert ist und diese Namensbestandteile nicht wie erwartet pflegt, sollte die Exportlogik an die konkrete pretix-Konfiguration angepasst werden.

## Für wen dieses Plugin gedacht ist

Das Plugin eignet sich für Organisationen, die aus pretix standardisierte Listen mit personenbezogenen Veranstaltungsdaten exportieren müssen und dabei eine feste Zielstruktur brauchen. Es ist besonders dann sinnvoll, wenn interne Referenzen in Formularen konsequent gepflegt werden und die Exportlogik dauerhaft stabil reproduzierbar sein soll.

## Entwicklungshinweise

pretix empfiehlt für spezialisierte Datenausgaben den Weg über Exporter-Plugins statt über frei gebaute Einzelviews. Exporter sind in der Plattform bereits dafür vorgesehen, Dateiformate bereitzustellen und zusätzliche Exportoptionen als Formularfelder anzubieten.

Das Plugin folgt außerdem dem üblichen pretix-Plugin-Aufbau mit Python-Paket, App-Konfiguration und Registrierung über `entry_points`. Dadurch lässt es sich sauber deployen, versionieren und in bestehende pretix-Setups integrieren.
