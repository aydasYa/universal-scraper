# Projekt einfach erklaert

Dieses Dokument erklaert das gesamte Projekt und die Ordnerstruktur.

Es ist fuer dich geschrieben, wenn du wenig Python-Erfahrung hast und trotzdem verstehen willst, was hier passiert.

## Was macht das Projekt?

Das Projekt sammelt Friseur- und Barbershop-Standorte in Deutschland.

Eine fertige Zeile soll immer ein echter physischer Standort sein.

Beispiel:

```text
Salon Beispiel
Musterstr 1
10115 Berlin
Telefon
Website
E-Mail, falls gefunden
Google Place ID
Suchbegriffe, ueber die der Standort gefunden wurde
```

Wichtig:

Gleiche Website oder gleiche zentrale E-Mail bedeutet nicht automatisch gleicher Standort.

Warum?

Eine Kette kann viele Standorte haben, aber dieselbe Website verwenden. Diese Standorte muessen getrennt bleiben.

## Die Pipeline als einfacher Ablauf

Man kann sich das Projekt wie eine Verarbeitungskette vorstellen.

### Schritt 1: Google Places findet Rohdaten

Quelle:

```text
Google Places API (New)
```

Aktive Suchbegriffe:

```text
Herrenfriseur
Barbershop
Damenfriseur
Friseursalon
```

Google wird pro Suchbegriff und Gebietskachel gefragt.

Die Rohdaten landen hier:

```text
data/raw/google_places/
```

### Schritt 2: Gleiche Google Place IDs werden zusammengefuehrt

Wenn derselbe Standort ueber mehrere Suchbegriffe gefunden wurde, soll er nur einmal in der finalen Liste stehen.

Dabei wird aber gespeichert, ueber welche Suchbegriffe er gefunden wurde.

Beispiel:

```text
erstfund_keyword: Herrenfriseur
gefunden_durch_suchbegriffe: Herrenfriseur, Barbershop
anzahl_suchbegriffe: 2
kw_herrenfriseur: True
kw_barbershop: True
```

### Schritt 3: Deduplizierung

Deduplizierung bedeutet: Duplikate erkennen und zusammenfuehren.

Das Projekt ist dabei konservativ.

Es wird nur automatisch zusammengefuehrt, wenn starke Signale vorliegen, zum Beispiel:

- gleiche Google Place ID
- gleiche genaue Adresse und sehr aehnlicher Name
- gleiche Adresse und gleiche Telefonnummer
- sehr nahe Koordinaten und sehr aehnlicher Name

Nicht ausreichend:

- gleiche Website
- gleiche Domain
- gleiche zentrale E-Mail

### Schritt 4: Relevanzbewertung

Das Projekt prueft, ob ein Treffer wahrscheinlich wirklich ein Friseur-/Barbershop-Standort ist.

Positive Signale:

- `hair_salon`
- `friseur`
- `friseursalon`
- `barbershop`
- `barber`

Unsichere Signale:

- `beauty_salon`
- `spa`
- `kosmetik`
- `nails`

Negative Signale:

- `car_repair`
- `restaurant`
- `dentist`
- `doctor`

### Schritt 5: Website-/E-Mail-Enrichment

Wenn Google eine Website liefert, kann das Projekt typische Seiten pruefen:

```text
Startseite
kontakt
impressum
ueber-uns
about
contact
```

Gesucht werden:

- sichtbare E-Mail-Adressen
- `mailto:`-Links

Das ist optional. Ohne E-Mail bleibt ein Standort trotzdem gueltig.

### Schritt 6: Export

Am Ende werden Excel-Dateien geschrieben.

Finale Dateien:

```text
data/final/alles_komplett.xlsx
data/final/manuelle_pruefung.xlsx
data/final/aussortiert.xlsx
data/reports/keyword_statistik.xlsx
```

## Die wichtigsten Befehle

### Befehlsuebersicht

```bash
python main.py commands
```

### Aus vorhandenen Rohdaten Excel-Dateien machen

```bash
python main.py export
```

Das ist der wichtigste Alltagsbefehl.

Er nutzt nur vorhandene Rohdaten und macht daraus neue Excel-Dateien.

### Zusaetzlich E-Mails suchen

```bash
python main.py enrich
```

Oder genauer:

```bash
python main.py enrich --contact-workers 4 --contact-timeout 5
```

### Kleiner sicherer Test

```bash
python main.py test
```

### Deutschlandlauf planen

```bash
python main.py plan
```

### Echter Deutschlandlauf

```bash
python main.py --country germany --full-run --resume
```

Dieser Befehl kann kostenpflichtige Google-API-Aufrufe ausloesen.

## Projektstruktur

Hier ist die wichtigste Ordnerstruktur.

```text
scraper-friseure/
  main.py
  run.py
  README.md
  AGENTS.md
  requirements.txt
  .env.example
  config/
    friseure.yaml
  scraper/
    config.py
    costs.py
    models.py
    pipeline.py
    storage.py
    discovery/
      google_places.py
    enrichment/
      contacts.py
    export/
      xlsx.py
    matching/
      deduplicate.py
      normalize.py
      relevance.py
  tests/
    test_pipeline.py
  data/
    raw/
      google_places/
    processed/
    final/
    reports/
    checkpoints/
```

## Was machen die Dateien?

### `main.py`

Sehr kleine Startdatei.

Sie ruft nur die eigentliche Bedienlogik in `run.py` auf.

Du startest fast immer:

```bash
python main.py ...
```

### `run.py`

Das ist die Kommandozentrale fuer Terminal-Befehle.

Hier wird entschieden:

- welcher Modus laeuft
- ob Google abgefragt wird
- ob nur vorhandene Rohdaten genutzt werden
- ob E-Mail-Enrichment laeuft
- welche Ordner benutzt werden
- wie Logs angezeigt werden

Beispiele:

```bash
python main.py export
python main.py plan
python main.py enrich
```

### `README.md`

Die Hauptanleitung fuer das Projekt.

### `AGENTS.md`

Interne Projektregeln fuer Codex/Agenten.

Dort steht zum Beispiel:

- aktive Branche ist `Friseure`
- aktive Quelle ist Google Places API (New)
- keine neuen Keywords ohne ausdrueckliche Entscheidung
- ein finaler Datensatz ist ein physischer Standort
- gleiche Domain allein niemals mergen

### `requirements.txt`

Liste der Python-Pakete, die das Projekt braucht.

Beispiele:

```text
beautifulsoup4
openpyxl
python-dotenv
PyYAML
requests
```

### `.env.example`

Beispiel fuer die lokale `.env`-Datei.

In der echten `.env` steht dein Google API Key:

```text
PLACES_API_KEY=...
```

Die echte `.env` sollte nicht ins Repository.

## Ordner `config/`

### `config/friseure.yaml`

Hier steht die aktive Branchen-Konfiguration.

Aktuell:

```yaml
slug: friseure
name: Friseure

search_terms:
  - Herrenfriseur
  - Barbershop
  - Damenfriseur
  - Friseursalon
```

Diese Suchbegriffe bestimmen, wonach bei Google gesucht wird.

## Ordner `scraper/`

Hier liegt der eigentliche Programmcode.

### `scraper/config.py`

Liest die YAML-Konfiguration.

Einfach gesagt:

Es macht aus `config/friseure.yaml` ein Python-Objekt, mit dem der Rest des Projekts arbeiten kann.

### `scraper/costs.py`

Schaetzt Google-API-Kosten.

Wird beim Befehl genutzt:

```bash
python main.py plan
```

### `scraper/models.py`

Definiert, wie ein Standort im Programm aussieht.

Der wichtigste Typ ist:

```text
PlaceRecord
```

Das ist ein einzelner Standort mit Feldern wie:

- Firmenname
- Strasse
- PLZ
- Ort
- Telefon
- Website
- E-Mail
- Google Place ID
- Suchbegriffe
- Klassifizierung

### `scraper/pipeline.py`

Das ist die Hauptverarbeitung.

Hier passiert:

- Rohdaten laden
- Google-Rohdaten in Standort-Datensaetze umwandeln
- Duplikate entfernen
- optional E-Mail-Suche starten
- Relevanz klassifizieren
- verarbeitete JSONL schreiben
- Excel-Dateien schreiben
- Keyword-Statistik schreiben

### `scraper/storage.py`

Hilfsdatei fuer sicheres Schreiben.

Warum wichtig?

Wenn ein Lauf abbricht, sollen Dateien nicht halb kaputt geschrieben werden.

Diese Datei macht:

- Checkpoint-Zeilen sicher anhaengen
- verarbeitete Dateien erst temporaer schreiben
- fertige Dateien atomar ersetzen

## Ordner `scraper/discovery/`

### `scraper/discovery/google_places.py`

Alles, was mit Google Places zu tun hat.

Hier stehen:

- Google API URL
- FieldMask
- Deutschland-Kacheln
- Berlin-Testkachel
- Checkpoint fuer Google-Discovery
- Retry-Logik bei API-Fehlern
- Speichern der Rohdaten

Rohdaten werden geschrieben nach:

```text
data/raw/google_places/
```

## Ordner `scraper/enrichment/`

### `scraper/enrichment/contacts.py`

Sucht E-Mail-Adressen auf Websites.

Es prueft typische Seiten wie:

```text
/
/kontakt
/impressum
/ueber-uns
/about
/contact
```

Es speichert Fortschritt hier:

```text
data/checkpoints/contact_enrichment.jsonl
```

Damit muss eine Website beim naechsten Lauf nicht nochmal geprueft werden.

## Ordner `scraper/export/`

### `scraper/export/xlsx.py`

Schreibt Excel-Dateien.

Diese Datei bestimmt:

- welche Spalten in den Excel-Dateien stehen
- welche Sheets erzeugt werden
- wie Spaltenbreiten gesetzt werden
- dass Header fett sind
- dass Filter aktiviert sind

## Ordner `scraper/matching/`

Hier geht es um Namen, Adressen, Duplikate und Relevanz.

### `scraper/matching/normalize.py`

Normalisiert Werte.

Das bedeutet:

Unterschiedliche Schreibweisen werden vergleichbarer gemacht.

Beispiele:

```text
"030 123456" -> "+4930123456"
"https://www.beispiel.de/" -> "https://beispiel.de"
"Musterstrasse 1" -> "musterstr"
```

### `scraper/matching/deduplicate.py`

Erkennt Duplikate.

Ziel:

Ein physischer Standort soll nur einmal in der finalen Liste stehen.

Aber:

Kettenstandorte mit gleicher Website bleiben getrennt.

### `scraper/matching/relevance.py`

Bewertet, ob ein Treffer wirklich relevant ist.

Moegliche Ergebnisse:

```text
komplett
manuelle_pruefung
aussortiert
```

## Ordner `tests/`

### `tests/test_pipeline.py`

Automatische Tests.

Sie pruefen wichtige Regeln, zum Beispiel:

- Google-Request sieht richtig aus
- gleiche Place ID wird gemerged
- gleiche Domain an anderer Adresse wird nicht gemerged
- Keyword-Provenienz bleibt erhalten
- Excel-Dateien werden erzeugt
- Contact-Checkpoint wird wiederverwendet
- kaputte JSONL-Zeilen stoppen den Lauf nicht
- Keyword-Statistik zeigt Ueberschneidungen

Tests starten:

```bash
python -m unittest discover
```

Oder mit deiner venv:

```bash
.venv/bin/python -m unittest discover
```

## Ordner `data/`

Dieser Ordner enthaelt Daten und Ergebnisse.

### `data/raw/google_places/`

Hier liegen die rohen Google-Ergebnisse.

Diese Dateien sind wichtig, weil du daraus jederzeit neue Excel-Dateien erzeugen kannst, ohne Google nochmal zu bezahlen.

Alltagsbefehl:

```bash
python main.py export
```

### `data/processed/`

Hier liegt eine verarbeitete Zwischenversion.

Datei:

```text
data/processed/standorte.jsonl
```

Das ist praktisch fuer Debugging oder spaetere Weiterverarbeitung.

### `data/final/`

Hier liegen die wichtigsten Excel-Dateien.

```text
alles_komplett.xlsx
manuelle_pruefung.xlsx
aussortiert.xlsx
```

### `data/reports/`

Hier liegen Auswertungen.

Wichtig:

```text
keyword_statistik.xlsx
```

Diese Datei zeigt, wie stark sich die Suchbegriffe ueberschneiden und welche Keywords zusaetzliche Treffer bringen.

### `data/checkpoints/`

Hier merkt sich das Projekt Fortschritt.

Wichtig:

```text
google_places.jsonl
contact_enrichment.jsonl
```

Checkpoints helfen nach Abbruechen.

## Was bedeuten die finalen Excel-Dateien?

### `alles_komplett.xlsx`

Standorte, die wahrscheinlich relevante Friseur-/Barbershop-Standorte sind.

Das ist die wichtigste finale Liste.

### `manuelle_pruefung.xlsx`

Faelle, die nicht sicher automatisch entschieden werden sollten.

Beispiele:

- moegliches Duplikat
- unklare Branche
- Beauty-/Kosmetik-Signal

Diese Liste sollte ein Mensch pruefen.

### `aussortiert.xlsx`

Treffer, die nicht in die Hauptliste gehoeren.

Beispiele:

- klare Duplikate
- irrelevante Branche
- dauerhaft geschlossen

## Was bedeutet Keyword-Provenienz?

Keyword-Provenienz bedeutet:

Das Projekt speichert, ueber welchen Suchbegriff ein Standort gefunden wurde.

Warum wichtig?

So sieht man spaeter:

- welcher Suchbegriff viele Treffer bringt
- welcher Suchbegriff nur Duplikate bringt
- welche Suchbegriffe zusammen wichtig sind

Wichtige Spalten:

```text
erstfund_keyword
gefunden_durch_suchbegriffe
anzahl_suchbegriffe
kw_herrenfriseur
kw_barbershop
kw_damenfriseur
kw_friseursalon
```

## Was tun bei Problemen?

### Es dauert lange

Wenn du E-Mail-Suche aktiviert hast, ist das normal.

Schneller Lauf ohne E-Mail-Suche:

```bash
python main.py export
```

### Ich habe abgebrochen

Einfach neu starten.

Bei vorhandenen Rohdaten:

```bash
python main.py export
```

Bei E-Mail-Suche:

```bash
python main.py enrich
```

Fertige Websites werden ueber den Checkpoint uebersprungen.

### Ich will keine Google-Kosten

Nutze:

```bash
python main.py export
```

oder:

```bash
python main.py plan
```

Nicht nutzen, wenn du keine API-Kosten willst:

```bash
python main.py --country germany --full-run --resume
```

### Ich will sehen, was passiert

Die CLI zeigt jetzt am Anfang:

- Laufmodus
- Suchbegriffe
- Rohdatenordner
- Outputordner
- Reportordner
- Google-Status
- E-Mail-Enrichment-Status
- Checkpoints

## Empfehlung fuer deinen Alltag

Meistens reicht:

```bash
python main.py export
```

Wenn du E-Mails willst:

```bash
python main.py enrich --contact-workers 4 --contact-timeout 5
```

Wenn du nur planen willst:

```bash
python main.py plan
```

