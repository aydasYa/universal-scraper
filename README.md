# Deutschlandweiter Friseur-Scraper

Robuste Pipeline fuer physische Friseur- und Barbershop-Standorte in Deutschland. Discovery erfolgt in Version 1 ausschliesslich ueber Google Places API (New).

Aktive Suchbegriffe aus [config/friseure.yaml](config/friseure.yaml):

- Herrenfriseur
- Barbershop
- Damenfriseur
- Friseursalon

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

In `.env` muss `PLACES_API_KEY` gesetzt werden. Secrets gehoeren nicht ins Repository.

## Pipeline

1. Places API (New) Text Search mit Deutschland-Raster, Pagination, FieldMask und Kachelsplitting
2. Keyword-Provenienz pro Google Place ID zusammenfuehren
3. Standorte konservativ deduplizieren
4. Friseur-Relevanz bewerten
5. Websites aus Google Places nach E-Mail-Adressen durchsuchen
6. Final klassifizieren
7. Drei getrennte XLSX-Dateien exportieren

Rohdaten liegen unter `data/raw/google_places/`. Aenderungen an Deduping, Klassifizierung oder XLSX-Export koennen daraus erneut verarbeitet werden, ohne Google erneut abzufragen.

## Klare Kurzbefehle

Die alten Flags funktionieren weiter. Fuer den Alltag sind diese Kurzbefehle einfacher:

```bash
python main.py commands
```

```bash
python main.py export
```

Verarbeitet vorhandene Rohdaten schnell zu Excel, ohne Google und ohne Website-Crawling.

```bash
python main.py enrich
```

Verarbeitet vorhandene Rohdaten zu Excel und durchsucht vorhandene Websites nach E-Mail-Adressen. Fortschritt wird im Contact-Checkpoint gespeichert.

```bash
python main.py test
```

Sicherer kleiner Berlin-Testlauf mit Google Places, `--limit-tiles 1` und `--resume`.

```bash
python main.py plan
```

Deutschlandlauf planen und Kosten schaetzen, ohne API-Aufrufe.

Der bewusste Deutschlandlauf bleibt absichtlich die explizite Langform, weil er kostenpflichtige Google-API-Aufrufe ausloesen kann:

```bash
python main.py --country germany --full-run --resume
```

Bei jedem Lauf zeigt die CLI jetzt Modus, Rohdatenordner, Outputordner, Reports, Discovery-Status, Checkpoints und E-Mail-Enrichment-Einstellungen an.

## Sicherer Testlauf

```bash
python main.py test
```

Plan anzeigen, ohne API-Kosten:

```bash
python main.py --test-region berlin --limit-tiles 1 --dry-run
```

Der Dry Run zeigt Suchmodus, Keywords, Kacheln, Mindestzahl der Text-Search-Abfragen und eine Google-Places-Kostenschaetzung. Der Standardlauf fragt Website und Telefonnummer direkt in Text Search (New) ab; dadurch wird die Text Search Enterprise SKU angesetzt und es werden keine separaten Place-Details-Abfragen pro Treffer kalkuliert.

Die API-Feldmaske steht in `scraper/discovery/google_places.py` als `TEXT_SEARCH_FIELD_MASK`. Sie enthaelt aktuell `places.id`, `places.displayName`, `places.formattedAddress`, `places.addressComponents`, `places.location`, `places.primaryType`, `places.types`, `places.businessStatus`, `places.googleMapsUri`, `places.websiteUri`, `places.nationalPhoneNumber`, `places.internationalPhoneNumber` und `nextPageToken`.

```bash
python main.py --country germany --full-run --dry-run
```

Nur vorhandene Rohdaten weiterverarbeiten:

```bash
python main.py export
```

## Bewusster Deutschlandlauf

Ein kompletter Lauf startet nur explizit:

```bash
python main.py --country germany --full-run --resume
```

Vor dem Start werden Suchbegriffe, Grundkacheln und die geschaetzte Mindestzahl an API-Abfragen angezeigt. Pagination und Splits koennen weitere kostenpflichtige Text-Search-Abfragen verursachen.

Waehrend der Discovery loggt die CLI aktuelles Keyword, Kachel-ID, Trefferzahl, neue/bekannte Place IDs, Gesamtzahl eindeutiger Places, Splits und Checkpoint-Status.

### Smart-Split gegen Rohduplikate

Bei sehr dichten Regionen wie Berlin kann Google in vielen Unterkacheln fast dieselben Standorte zurueckgeben. Deshalb ist `Smart-Split` standardmaessig aktiv.

Eine dichte Unterkachel wird nur weiter geteilt, wenn sie fuer denselben Suchbegriff genug neue Google Place IDs bringt.

Standard:

```bash
--split-min-new-place-ids 8 --split-min-new-ratio 0.15
```

Das bedeutet: Eine Unterkachel wird weiter geteilt, wenn sie mindestens 8 neue Place IDs oder mindestens 15 Prozent neue Place IDs liefert.

Maximale, alte Suchbreite erzwingen:

```bash
python main.py --country germany --full-run --resume --no-smart-split
```

Das kann mehr Treffer in Grenzfaellen finden, erzeugt aber deutlich mehr Rohduplikate und API-Aufrufe.

## Resume und Checkpoints

Google-Checkpoints werden unter `data/checkpoints/google_places.jsonl` gespeichert. Der Schluessel besteht aus `keyword + tile`. Mit `--resume` werden erfolgreiche Keyword/Kachel-Kombinationen uebersprungen.

Contact-Checkpoints werden unter `data/checkpoints/contact_enrichment.jsonl` gespeichert. Bereits gepruefte Websites werden beim naechsten Lauf wiederverwendet, auch wenn keine E-Mail gefunden wurde.

Abbruchverhalten:

- `Ctrl-C` beendet die CLI ohne langen Python-Traceback.
- Fertige Google-Kacheln und fertig gepruefte Websites bleiben durch Checkpoints erhalten.
- Wenn beim Resume eine fertige Google-Kachel mit Unterteilung uebersprungen wird, werden ihre Unterkacheln wieder in die Warteschlange gelegt.
- Rohdaten, verarbeitete JSONL-Dateien und XLSX-Exports werden atomar geschrieben. Ein Abbruch ersetzt finale Dateien erst, wenn die neue Datei vollstaendig geschrieben wurde.
- Beschadigte Restzeilen in JSONL-Dateien aus alten Abbruechen werden beim Lesen uebersprungen und als Warnung geloggt.

## Outputs

Der Hauptoutput besteht aus drei getrennten Dateien:

- `data/final/alles_komplett.xlsx`: akzeptierte relevante Friseur-/Barbershop-Standorte
- `data/final/manuelle_pruefung.xlsx`: unsichere Branchen- oder Dedup-Faelle
- `data/final/aussortiert.xlsx`: klare irrelevante, geschlossene oder verworfene Duplikate

Zusaetzlich entsteht `data/reports/keyword_statistik.xlsx` mit Recall-Statistik je Suchbegriff. Die Datei enthaelt neben der Gesamtzahl `auch_ueber_andere_keywords` jetzt auch:

- `auch_ueber_andere_keywords_details`: andere Keywords mit Anzahl, z.B. `Barbershop: 120; Damenfriseur: 40`
- `keyword_kombinationen_details`: Kombinationen der Suchbegriffe mit Anzahl
- `auch_kw_herrenfriseur`, `auch_kw_barbershop`, `auch_kw_damenfriseur`, `auch_kw_friseursalon`: numerische Ueberschneidungen je Keyword

## Keyword-Provenienz

Jeder Standort behaelt `erstfund_keyword`, `gefunden_durch_suchbegriffe`, `anzahl_suchbegriffe` und die vier Boolean-Spalten `kw_herrenfriseur`, `kw_barbershop`, `kw_damenfriseur`, `kw_friseursalon`.

## Deduplizierung

Eine Zeile entspricht einem physischen Standort. Gleiche Google Place ID wird automatisch zusammengefuehrt. Weitere automatische Merges erfolgen nur bei starken Kombinationen aus Adresse, Name, Telefon oder Koordinaten. Gleiche Website-Domain allein ist niemals ein Duplikat-Signal; Kettenstandorte bleiben getrennt.

## Kontakt-Enrichment

Wenn Google Places eine Website liefert, werden Startseite und typische Kontakt-/Impressumsseiten per HTTP durchsucht. Erkannt werden `mailto:` und sichtbare E-Mail-Adressen. Fehlende E-Mail disqualifiziert keinen Standort.

Der Fortschritt wird unter `data/checkpoints/contact_enrichment.jsonl` gecached. Ein Abbruch waehrend des E-Mail-Crawlings verliert dadurch beim naechsten Lauf nicht mehr alle bereits geprueften Websites. Langsame Websites werden mit kurzem Timeout uebersprungen.

Steuerbare Optionen:

```bash
python main.py enrich --contact-timeout 5 --contact-workers 4 --contact-checkpoint data/checkpoints/contact_enrichment.jsonl
```

Terminalmeldungen:

```text
INFO contact enrichment pending websites=1114 records=1114 workers=4 timeout=5s
INFO contact checkpoint done website=1/1114 records=1 url=https://www.example.de email=info@example.de
INFO contact checkpoint skip 1605/1759 website=https://www.example.de email=yes
```

## Tests

```bash
python -m unittest discover
```

Die Tests nutzen Fixtures und starten keine echte Google-API-Suche.
