# Agent Notes

Ziel: deutschlandweiter Scraper fuer physische Friseur-/Barbershop-Standorte. Aktive Branche ist `Friseure`, konfiguriert in `config/friseure.yaml`.

Aktive Discovery-Quelle: ausschliesslich Google Places API (New), konkret Text Search (New) mit FieldMask. Aktive Keywords: `Herrenfriseur`, `Barbershop`, `Damenfriseur`, `Friseursalon`. Keine weiteren Discovery-Keywords ohne explizite Nutzerentscheidung hinzufuegen.

Pipeline: Google Discovery -> Keyword-Merge -> konservative Standort-Deduplizierung -> Relevanzbewertung -> Website/E-Mail-Enrichment -> Klassifizierung -> XLSX-Export.

Eine finale Zeile entspricht immer einem physischen Standort. Gleiche Domain oder gleiche zentrale E-Mail allein niemals mergen. Kettenstandorte mit gleicher Website muessen getrennt bleiben.

Keyword-Provenienz niemals verlieren: `erstfund_keyword`, `gefunden_durch_suchbegriffe`, `anzahl_suchbegriffe`, `kw_herrenfriseur`, `kw_barbershop`, `kw_damenfriseur`, `kw_friseursalon`.

Outputs:

- `data/final/alles_komplett.xlsx`
- `data/final/manuelle_pruefung.xlsx`
- `data/final/aussortiert.xlsx`
- `data/reports/keyword_statistik.xlsx`

Tests:

```bash
python -m unittest discover
```

Sicherer Testlauf:

```bash
python main.py test
```

Kosten/Plan ohne API-Aufruf:

```bash
python main.py plan
```

Bewusster Full Run:

```bash
python main.py --country germany --full-run --resume
```

Keinen deutschlandweiten Google-Lauf ohne `--country germany --full-run` starten. Rohdaten unter `data/raw/google_places/` vor erneuten API-Aufrufen bevorzugen. Schneller Rohdaten-Export: `python main.py export`. Rohdaten plus Website/E-Mail-Enrichment: `python main.py enrich`. Google-Discovery-Checkpoints liegen unter `data/checkpoints/google_places.jsonl`. Discovery nutzt standardmaessig Smart-Split (`--split-min-new-place-ids 8 --split-min-new-ratio 0.15`), damit dichte Unterkacheln mit fast nur bekannten Place IDs nicht weiter gesplittet werden; alte maximale Breite nur bewusst mit `--no-smart-split`. Contact-Enrichment nutzt normale Website-Requests, keine Google-API, und cached Fortschritt unter `data/checkpoints/contact_enrichment.jsonl`. Optionen: `--contact-timeout`, `--contact-workers`, `--contact-checkpoint`.
