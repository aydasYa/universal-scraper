# Aenderungen einfach erklaert

Dieses Dokument erklaert die letzten Verbesserungen am Projekt in einfacher Sprache.

Du musst dafuer kein Python koennen. Wichtig ist vor allem: Welche Befehle gibt es jetzt, was wurde sicherer gemacht, und warum laeuft es schneller?

## Kurzfassung

Vorher konnte der Befehl lange so wirken, als ob nichts passiert. Beim Abbruch mit `Ctrl-C` kam dann ein langer Python-Traceback. Die Ursache war hauptsaechlich eine langsame Duplikat-Pruefung.

Jetzt ist das Projekt robuster:

- Es gibt einfache Befehle wie `python main.py export`, `python main.py enrich`, `python main.py plan`.
- Die Duplikat-Pruefung ist stark beschleunigt.
- Bei `Ctrl-C` kommt kein riesiger Fehlertext mehr.
- Zwischenergebnisse werden besser gesichert.
- Excel-Dateien werden erst ersetzt, wenn sie komplett geschrieben sind.
- Der Keyword-Report zeigt jetzt genauer, welche Suchbegriffe sich ueberschneiden.
- Google-Discovery hat jetzt eine Smart-Split-Bremse gegen sehr viele Rohduplikate.

## Die wichtigsten neuen Befehle

### 1. Befehle anzeigen

```bash
python main.py commands
```

Zeigt eine kurze Uebersicht der wichtigsten Befehle.

### 2. Vorhandene Rohdaten schnell zu Excel machen

```bash
python main.py export
```

Das ist der beste Standardbefehl, wenn schon Google-Rohdaten vorhanden sind.

Er macht:

- keine neue Google-Abfrage

- schnelle Verarbeitung der vorhandenen Dateien
- neue Excel-Dateien in `data/final/`
- neuen Keyword-Report in `data/reports/`

### 3. Vorhandene Rohdaten plus E-Mail-Suche

```bash
python main.py enrich
```

Das macht wie `export` die Excel-Dateien, sucht aber zusaetzlich auf Websites nach E-Mail-Adressen.

Das kann laenger dauern, weil viele Websites langsam oder kaputt sein koennen.

Steuerung:

```bash
python main.py enrich --contact-workers 4 --contact-timeout 5
```

Bedeutung:

- `--contact-workers 4`: bis zu 4 Websites gleichzeitig pruefen
- `--contact-timeout 5`: pro Website-Seite maximal 5 Sekunden warten

### 4. Kostenlosen Plan anzeigen

```bash
python main.py plan
```

Zeigt, wie viele Google-Abfragen fuer Deutschland geplant waeren und was das grob kosten koennte.

Wichtig: Dieser Befehl macht keine echten API-Abfragen.

### 5. Sicherer kleiner Test

```bash
python main.py test
```

Startet einen kleinen Berlin-Testlauf.

### 6. Echter Deutschlandlauf

```bash
python main.py --country germany --full-run --resume
```

Dieser Befehl bleibt absichtlich lang, weil er kostenpflichtige Google-API-Aufrufe ausloesen kann.

## Was ist Smart-Split?

Bei sehr dichten Regionen wie Berlin teilt das Tool eine grosse Suchkachel in kleinere Unterkacheln.

Das ist gut, weil Google sonst oft nur die ersten Treffer zeigt.

Aber:

Manche Unterkacheln liefern fast nur dieselben Standorte wie vorher.

Vorher wurden solche Unterkacheln trotzdem weiter geteilt. Dadurch entstanden viele Rohduplikate und mehr Google-Abfragen.

Jetzt prueft Smart-Split:

```text
Bringt diese Unterkachel wirklich genug neue Google Place IDs?
```

Standard:

```bash
--split-min-new-place-ids 8 --split-min-new-ratio 0.15
```

Bedeutung:

- mindestens 8 neue Place IDs
- oder mindestens 15 Prozent neue Place IDs

Nur dann wird eine dichte Unterkachel weiter geteilt.

Wenn du ausnahmsweise die alte maximale Suchbreite willst:

```bash
python main.py --country germany --full-run --resume --no-smart-split
```

Das kann mehr API-Aufrufe und mehr Rohduplikate erzeugen.

## Was wurde an der Performance verbessert?

### Vorher

Bei der Duplikat-Pruefung wurde fast jeder Eintrag mit fast jedem anderen Eintrag verglichen.

Bei vielen Daten bedeutet das sehr viele Vergleiche.

Beispiel:

- 20.400 Rohdatensaetze
- jeder wird gegen viele andere geprueft
- jeder Vergleich nutzt teilweise eine teure Namensaehnlichkeit

Das wurde immer langsamer, je mehr Daten vorhanden waren.

### Jetzt

Jetzt wird zuerst gefragt:

- gleiche Google Place ID?
- gleiche genaue Adresse?
- gleiche Telefonnummer?
- sehr nahe Koordinaten?

Nur wenn so ein starkes Signal vorhanden ist, wird ein genauer Vergleich gemacht.

Dadurch bleibt die Logik konservativ, aber sie ist viel schneller.

Gemessener Kerncheck auf den vorhandenen Daten:

- Rohdaten: 20.400
- eindeutige Standorte: 1.759
- Deduplizierung: ca. 0,07 Sekunden

## Was wurde fuer Abbrueche verbessert?

### Problem

Bei langen Laeufen kann immer etwas passieren:

- Terminal wird geschlossen
- Internet bricht ab
- Google API antwortet kurz nicht
- Website haengt
- `Ctrl-C` wird gedrueckt
- Excel-Datei wird gerade geschrieben

### Neue Schutzmassnahmen

#### 1. Freundlicher Abbruch

Wenn du `Ctrl-C` drueckst, kommt keine lange Python-Fehlermeldung mehr.

Stattdessen kommt ein kurzer Hinweis, dass fertige Checkpoints erhalten bleiben.

#### 2. Checkpoints werden sofort gespeichert

Google-Discovery:

```text
data/checkpoints/google_places.jsonl
```

Website-/E-Mail-Suche:

```text
data/checkpoints/contact_enrichment.jsonl
```

Wenn ein Schritt fertig ist, wird er sofort in den Checkpoint geschrieben.

Beim naechsten Lauf kann `--resume` diese fertigen Schritte ueberspringen.

Wenn eine fertige Google-Kachel beim Resume bereits als `split=True` markiert ist, werden ihre Unterkacheln wieder in die Warteschlange gelegt. Dadurch geht ein Abbruch direkt nach einer Eltern-Kachel nicht mehr verloren.

#### 3. Excel-Dateien werden atomar geschrieben

Das bedeutet:

Die bestehende Excel-Datei wird nicht halb ueberschrieben.

Stattdessen wird erst eine temporaere Datei geschrieben. Erst wenn sie vollstaendig fertig ist, ersetzt sie die alte Datei.

Das schuetzt zum Beispiel:

```text
data/final/alles_komplett.xlsx
data/final/manuelle_pruefung.xlsx
data/final/aussortiert.xlsx
data/reports/keyword_statistik.xlsx
```

#### 4. Kaputte JSONL-Restzeilen werden uebersprungen

Wenn ein alter Lauf mitten beim Schreiben abgebrochen wurde, kann am Ende einer Datei eine halbe JSON-Zeile stehen.

Frueher konnte das den Lauf stoppen.

Jetzt wird so eine kaputte Zeile uebersprungen und als Warnung geloggt.

## Was wurde am Keyword-Report verbessert?

Datei:

```text
data/reports/keyword_statistik.xlsx
```

Vorher gab es die Spalte:

```text
auch_ueber_andere_keywords
```

Die sagte nur, wie viele Place IDs auch ueber andere Suchbegriffe gefunden wurden.

Jetzt gibt es zusaetzlich:

```text
auch_ueber_andere_keywords_details
keyword_kombinationen_details
auch_kw_herrenfriseur
auch_kw_barbershop
auch_kw_damenfriseur
auch_kw_friseursalon
```

### Beispiel

Wenn bei `Herrenfriseur` steht:

```text
auch_ueber_andere_keywords_details:
Barbershop: 383; Damenfriseur: 498; Friseursalon: 493
```

Dann bedeutet das:

- 383 der Herrenfriseur-Treffer wurden auch ueber `Barbershop` gefunden
- 498 wurden auch ueber `Damenfriseur` gefunden
- 493 wurden auch ueber `Friseursalon` gefunden

Die Spalte `keyword_kombinationen_details` zeigt, welche Kombinationen vorkommen.

Beispiel:

```text
Herrenfriseur + Barbershop: 254
Herrenfriseur + Damenfriseur + Friseursalon: 370
```

Das hilft zu verstehen, welche Suchbegriffe viel doppelt finden und welche wirklich neue Standorte bringen.

## Was wurde an der Website-/E-Mail-Suche verbessert?

Vorher konnte dieselbe Website mehrfach geprueft werden, wenn mehrere Standorte dieselbe Website hatten.

Jetzt wird eine normalisierte Website nur einmal geprueft.

Beispiel:

```text
https://www.salon.example
https://salon.example
```

Diese werden als gleiche Website behandelt.

Das spart Zeit und macht den Checkpoint nuetzlicher.

## Welche Dateien wurden geaendert?

### `run.py`

Hier sitzt die Bedienung ueber das Terminal.

Neu:

- einfache Befehle wie `export`, `enrich`, `plan`
- bessere Hilfe mit `python main.py --help`
- bessere Start-Zusammenfassung
- freundlicher `Ctrl-C`-Abbruch

### `scraper/matching/deduplicate.py`

Hier sitzt die Duplikat-Erkennung.

Neu:

- schneller Kandidaten-Index
- Vergleiche nur bei plausiblen Standort-Signalen
- gleiche Domains werden weiterhin nicht zum Mergen verwendet

### `scraper/pipeline.py`

Hier laeuft die Hauptverarbeitung.

Neu:

- mehr Fortschritts-Logs
- kaputte JSONL-Zeilen werden uebersprungen
- Keyword-Statistik mit Detail-Aufschluesselung
- atomarer Schreibvorgang fuer verarbeitete Daten

### `scraper/enrichment/contacts.py`

Hier sitzt die Website-/E-Mail-Suche.

Neu:

- parallele Website-Pruefung
- gleiche Website nur einmal pruefen
- robuster Contact-Checkpoint

### `scraper/export/xlsx.py`

Hier werden die Excel-Dateien geschrieben.

Neu:

- Excel-Dateien werden atomar gespeichert
- Keyword-Report hat neue Detailspalten

### `scraper/storage.py`

Neue Hilfsdatei fuer sicheres Schreiben.

Sie kuemmert sich um:

- JSONL sicher anhaengen
- Textdateien atomar ersetzen
- Excel-Dateien atomar ersetzen

### `README.md`

Die Anleitung wurde aktualisiert.

### `AGENTS.md`

Die internen Projekt-Notizen wurden aktualisiert.

### `.env.example`

Beispieldatei fuer die API-Key-Konfiguration.

## Welche Tests wurden ergaenzt?

In `tests/test_pipeline.py` wurden Tests ergaenzt fuer:

- Keyword-Report-Aufschluesselung
- kaputte JSONL-Zeilen
- Website-Enrichment mit gleicher Website nur einmal

Finaler Test:

```bash
.venv/bin/python -m unittest discover
```

Ergebnis:

```text
Ran 15 tests
OK
```

## Was sollst du im Alltag nutzen?

Wenn du nur Excel aus vorhandenen Rohdaten willst:

```bash
python main.py export
```

Wenn du zusaetzlich E-Mails suchen willst:

```bash
python main.py enrich --contact-workers 4 --contact-timeout 5
```

Wenn du erst wissen willst, was ein Deutschlandlauf kosten koennte:

```bash
python main.py plan
```

Wenn du wirklich deutschlandweit neue Google-Daten holen willst:

```bash
python main.py --country germany --full-run --resume
```
