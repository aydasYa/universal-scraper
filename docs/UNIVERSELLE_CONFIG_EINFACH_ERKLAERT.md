# Universelle Config einfach erklaert

Dieses Projekt ist in dieser Kopie nicht mehr fest auf Friseure verdrahtet.

Du steuerst die aktive Suche ueber:

```text
config/active.yaml
```

## Wichtigste Idee

Ein Projekt ist nicht ein einzelner Suchbegriff.

Ein Projekt ist ein Suchprofil mit mehreren Suchbegriffen.

Beispiel Friseursalons:

```text
Projekt: Friseursalons Deutschland
Suchbegriffe:
- Herrenfriseur
- Barbershop
- Damenfriseur
- Friseursalon
```

Beispiel Juweliere:

```text
Projekt: Juweliere Deutschland
Suchbegriffe:
- Juwelier
- Goldschmied
- Schmuckgeschaeft
- Trauringe
- Uhren Schmuck
```

## Minimal gueltige Config

Das reicht schon:

```yaml
project:
  slug: juweliere_de
  name: Juweliere Deutschland

search:
  terms:
    - Juwelier
    - Goldschmied
```

Pflichtfelder:

- `project.slug`
- `project.name`
- `search.terms`

## Was bedeutet `slug`?

Der `slug` ist der technische Ordnername.

Beispiel:

```yaml
project:
  slug: juweliere_de
```

Dann schreibt das Projekt automatisch nach:

```text
data/projects/juweliere_de/raw/google_places/
data/projects/juweliere_de/processed/
data/projects/juweliere_de/final/
data/projects/juweliere_de/reports/
data/projects/juweliere_de/checkpoints/
```

Damit vermischen sich Friseur- und Juwelierdaten nicht.

## Empfohlene vollere Config

```yaml
project:
  slug: juweliere_de
  name: Juweliere Deutschland
  category: juweliere

search:
  terms:
    - Juwelier
    - Goldschmied
    - Schmuckgeschaeft
    - Trauringe
    - Uhren Schmuck

google:
  included_type: jewelry_store

relevance:
  positive_terms:
    - jewelry_store
    - juwelier
    - goldschmied
    - schmuck

  uncertain_terms:
    - accessoires
    - mode

  negative_terms:
    - pawn_shop
    - bank
```

## Was ist optional?

Diese Felder duerfen fehlen:

```text
project.category
google.included_type
relevance.positive_terms
relevance.uncertain_terms
relevance.negative_terms
```

Wenn `google.included_type` fehlt:

```text
Google sucht nur mit Text, ohne Type-Filter.
```

Wenn `positive_terms` fehlt:

```text
Die Suchbegriffe und optional der Google-Type zaehlen als positive Signale.
```

Wenn `uncertain_terms` fehlt:

```text
Es gibt keine unsicheren Begriffe.
```

Wenn `negative_terms` fehlt:

```text
Es gibt keine negativen Begriffe.
```

## Suchprofil wechseln

Vorlagen liegen hier:

```text
config/examples/friseursalons_de.yaml
config/examples/juweliere_de.yaml
```

Zum Wechseln kannst du den Inhalt einer Vorlage in diese Datei uebernehmen:

```text
config/active.yaml
```

Danach funktionieren die normalen Befehle:

```bash
python main.py plan
python main.py export
python main.py enrich
python main.py --country germany --full-run --resume
```

## Welche Datenordner werden genutzt?

Immer passend zum aktiven `slug`.

Wenn aktiv:

```yaml
project:
  slug: friseursalons_de
```

dann:

```text
data/projects/friseursalons_de/
```

Wenn aktiv:

```yaml
project:
  slug: juweliere_de
```

dann:

```text
data/projects/juweliere_de/
```

## Warum nicht mehr `data/raw/google_places/`?

Der alte Ordner war gut, solange es nur Friseure gab.

Mit mehreren Suchprofilen waere das gefaehrlich, weil sich Daten vermischen koennten.

Deshalb jetzt:

```text
data/projects/<slug>/
```

## Beispiel: Juweliere suchen

1. `config/active.yaml` auf Juweliere stellen.
2. Erst Kosten planen:

```bash
python main.py plan
```

3. Wenn wirklich Google abgefragt werden soll:

```bash
python main.py --country germany --full-run --resume
```

4. Wenn Rohdaten vorhanden sind:

```bash
python main.py export
```

5. Wenn E-Mails gesucht werden sollen:

```bash
python main.py enrich --contact-workers 4 --contact-timeout 10
```

