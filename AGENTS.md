# Agent Notes

Ziel: universeller deutschlandweiter Scraper fuer physische lokale Unternehmensstandorte. Das aktive Suchprofil steht in `config/active.yaml`; Beispiele liegen unter `config/examples/`.

Aktive Discovery-Quelle: Google Places API (New), konkret Text Search (New) mit FieldMask. Aktive Keywords immer aus `search.terms` in `config/active.yaml` lesen. Keine weiteren Discovery-Keywords ohne explizite Nutzerentscheidung hinzufuegen.

Pipeline: Google Discovery -> Keyword-Merge -> konservative Standort-Deduplizierung -> Relevanzbewertung -> Website/E-Mail-Enrichment -> Klassifizierung -> XLSX-Export.

Eine finale Zeile entspricht immer einem physischen Standort. Gleiche Domain oder gleiche zentrale E-Mail allein niemals mergen. Kettenstandorte mit gleicher Website muessen getrennt bleiben.

Keyword-Provenienz niemals verlieren: `erstfund_keyword`, `gefunden_durch_suchbegriffe`, `anzahl_suchbegriffe`, plus automatische `kw_*`-Spalten fuer alle aktiven Suchbegriffe.

Outputs:

- `data/projects/<slug>/final/alles_komplett.xlsx`
- `data/projects/<slug>/final/manuelle_pruefung.xlsx`
- `data/projects/<slug>/final/aussortiert.xlsx`
- `data/projects/<slug>/reports/keyword_statistik.xlsx`

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

Keinen deutschlandweiten Google-Lauf ohne `--country germany --full-run` starten. Rohdaten unter `data/projects/<slug>/raw/google_places/` vor erneuten API-Aufrufen bevorzugen. Schneller Rohdaten-Export: `python main.py export`. Rohdaten plus Website/E-Mail-Enrichment: `python main.py enrich`. Google-Discovery-Checkpoints liegen unter `data/projects/<slug>/checkpoints/google_places.jsonl`. Discovery nutzt standardmaessig Smart-Split (`--split-min-new-place-ids 8 --split-min-new-ratio 0.15`), damit dichte Unterkacheln mit fast nur bekannten Place IDs nicht weiter gesplittet werden; alte maximale Breite nur bewusst mit `--no-smart-split`. Contact-Enrichment nutzt normale Website-Requests, keine Google-API, und cached Fortschritt unter `data/projects/<slug>/checkpoints/contact_enrichment.jsonl`. Optionen: `--contact-timeout`, `--contact-workers`, `--contact-checkpoint`.
