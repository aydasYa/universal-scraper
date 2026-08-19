from __future__ import annotations

import argparse
import logging
import sys
from textwrap import dedent

from dotenv import load_dotenv

from scraper.config import load_config
from scraper.costs import estimate_google_places_cost, format_cost_report
from scraper.discovery.google_places import berlin_test_tiles, discover_google_places, germany_tiles
from scraper.pipeline import process_raw_to_outputs


COMMAND_GUIDE = """\
Empfohlene Aufrufe:
  python main.py commands
      Zeigt diese Kurzuebersicht.

  python main.py export
      Vorhandene Google-Rohdaten schnell zu Excel verarbeiten, ohne Website-Crawling.

  python main.py enrich
      Vorhandene Google-Rohdaten zu Excel verarbeiten und Websites nach E-Mails durchsuchen.

  python main.py test
      Sicherer kleiner Berlin-Testlauf mit Google Places und Resume.

  python main.py plan
      Deutschlandlauf planen und Kosten schaetzen, ohne API-Aufruf.

  python main.py --country germany --full-run --resume
      Bewusster Deutschlandlauf mit Resume. Diese Langform bleibt absichtlich explizit,
      weil sie kostenpflichtige Google-API-Aufrufe ausloesen kann.

Kompatible Langform-Beispiele:
  python main.py --skip-discovery --skip-email
  python main.py --skip-discovery --contact-timeout 5 --contact-workers 4
  python main.py --test-region berlin --limit-tiles 1 --resume
  python main.py --country germany --full-run --dry-run
  python main.py --country germany --full-run --resume

Discovery-Feintuning:
  --no-smart-split
      Schaltet die Duplikat-/Kostenbremse beim Kachelsplitting aus.
  --split-min-new-place-ids 8 --split-min-new-ratio 0.15
      Eine dichte Unterkachel wird nur weiter geteilt, wenn sie genug neue Place IDs liefert.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deutschlandweiter Google-Places-Friseur-Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(COMMAND_GUIDE),
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["commands", "export", "enrich", "test", "plan"],
        help="Einfacher Modus. Nutze 'commands' fuer die wichtigsten Aufrufe.",
    )
    parser.add_argument("--config", default="config/friseure.yaml", help="Branchen-Konfiguration mit den aktiven Suchbegriffen.")
    parser.add_argument("--raw-dir", default="data/raw/google_places", help="Ordner mit Google-Places-Rohdaten.")
    parser.add_argument("--processed-dir", default="data/processed", help="Ordner fuer verarbeitete JSONL-Daten.")
    parser.add_argument("--final-dir", default="data/final", help="Ordner fuer finale XLSX-Dateien.")
    parser.add_argument("--reports-dir", default="data/reports", help="Ordner fuer Reports wie keyword_statistik.xlsx.")
    parser.add_argument("--test-region", choices=["berlin"], help="Sicherer kleiner Testlauf.")
    parser.add_argument("--country", choices=["germany"], help="Zielland fuer bewussten Full Run.")
    parser.add_argument("--full-run", action="store_true", help="Muss fuer den Deutschlandlauf explizit gesetzt werden.")
    parser.add_argument("--dry-run", action="store_true", help="Nur geplante Abfragen anzeigen, keine API anfragen.")
    parser.add_argument("--limit-tiles", type=int, help="Maximale Anzahl Basiskacheln pro Keyword.")
    parser.add_argument("--resume", action="store_true", help="Erfolgreiche Keyword/Kachel-Checkpoints ueberspringen.")
    parser.add_argument("--skip-discovery", action="store_true", help="Nur vorhandene Rohdaten weiterverarbeiten.")
    parser.add_argument("--skip-email", action="store_true", help="Website-Crawling fuer E-Mail-Adressen ueberspringen.")
    parser.add_argument(
        "--google-checkpoint",
        default="data/checkpoints/google_places.jsonl",
        help="JSONL-Checkpoint-Datei fuer Google-Places-Discovery.",
    )
    parser.add_argument(
        "--no-smart-split",
        dest="smart_split",
        action="store_false",
        help="Dichte Unterkacheln auch dann weiter teilen, wenn sie kaum neue Place IDs liefern.",
    )
    parser.set_defaults(smart_split=True)
    parser.add_argument(
        "--split-min-new-place-ids",
        type=int,
        default=8,
        help="Mindestzahl neuer Place IDs, damit eine dichte Unterkachel weiter geteilt wird.",
    )
    parser.add_argument(
        "--split-min-new-ratio",
        type=float,
        default=0.15,
        help="Mindestanteil neuer Place IDs, damit eine dichte Unterkachel weiter geteilt wird.",
    )
    parser.add_argument("--contact-timeout", type=int, default=5, help="Timeout pro Website-Unterseite im E-Mail-Enrichment.")
    parser.add_argument("--contact-workers", type=int, default=4, help="Parallele Website-Pruefungen fuer E-Mail-Enrichment.")
    parser.add_argument(
        "--contact-checkpoint",
        default="data/checkpoints/contact_enrichment.jsonl",
        help="JSONL-Checkpoint-Datei fuer E-Mail-Enrichment.",
    )
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Detailgrad der Logs.")
    parser.add_argument(
        "--ignore-free-cap",
        action="store_true",
        help="Kosten ohne monatlichen Google-Free-Cap schaetzen.",
    )
    return parser.parse_args()


def print_command_guide() -> None:
    print(dedent(COMMAND_GUIDE).strip())


def apply_command_defaults(args: argparse.Namespace) -> None:
    if args.command == "export":
        args.skip_discovery = True
        args.skip_email = True
    elif args.command == "enrich":
        args.skip_discovery = True
        args.skip_email = False
    elif args.command == "test":
        args.test_region = args.test_region or "berlin"
        args.limit_tiles = args.limit_tiles or 1
        args.resume = True
    elif args.command == "plan":
        args.country = args.country or "germany"
        args.full_run = True
        args.dry_run = True


def print_run_summary(args: argparse.Namespace, config, tiles: list, planned: int) -> None:
    mode = args.command or "flags"
    print(f"Laufmodus: {mode}")
    print("Suchbegriffe:", ", ".join(config.search_terms))
    print("Rohdaten:", args.raw_dir)
    print("Outputs:", args.final_dir)
    print("Reports:", args.reports_dir)
    if args.skip_discovery:
        print("Google Discovery: aus, vorhandene Rohdaten werden genutzt.")
    else:
        if args.dry_run:
            print("Google Discovery: geplant, aber im Dry Run kein API-Aufruf.")
        else:
            print("Google Discovery: an.")
        print("Grundkacheln:", len(tiles))
        print("Geschaetzte Mindestzahl API-Abfragen:", planned)
        print("Google-Checkpoint:", args.google_checkpoint)
        if args.smart_split:
            print(
                "Smart-Split: an "
                f"(min neue Place IDs={args.split_min_new_place_ids}, min Anteil={args.split_min_new_ratio:.2f})."
            )
        else:
            print("Smart-Split: aus.")
    if args.dry_run:
        print("E-Mail-Enrichment: aus im Dry Run.")
    elif args.skip_email:
        print("E-Mail-Enrichment: aus.")
    else:
        print(f"E-Mail-Enrichment: an, timeout={args.contact_timeout}s, workers={max(1, args.contact_workers)}.")
        print("Contact-Checkpoint:", args.contact_checkpoint)
    sys.stdout.flush()


def _main() -> int:
    args = parse_args()
    if args.command == "commands":
        print_command_guide()
        return 0

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(message)s", stream=sys.stdout)
    load_dotenv()
    apply_command_defaults(args)
    config = load_config(args.config)
    if args.test_region == "berlin":
        tiles = berlin_test_tiles()
    elif args.country == "germany" and args.full_run:
        tiles = germany_tiles()
    elif args.skip_discovery:
        tiles = []
    else:
        raise SystemExit("Kein Full Run ohne --country germany --full-run. Fuer Tests: --test-region berlin.")

    planned = len(config.search_terms) * (args.limit_tiles or len(tiles))
    print_run_summary(args, config, tiles, planned)
    if not args.skip_discovery:
        estimate = estimate_google_places_cost(
            text_search_requests=planned,
            details_requests=0,
            include_monthly_free_cap=not args.ignore_free_cap,
        )
        print("Suche: Places API (New) Text Search pro Suchbegriff und Geo-Kachel.")
        print("Felder: Name, Adresse, Koordinaten, Typen, Status, Google-Maps-Link, Website, Telefon.")
        print("Hinweis: Website/Telefon-Felder triggern in Places API (New) die Text Search Enterprise SKU.")
        print(format_cost_report(estimate))
        print("Hinweis: Pagination und Kachelsplits koennen weitere Text-Search-Abfragen erzeugen.")
        sys.stdout.flush()
    if args.dry_run:
        print("Dry Run: keine API-Aufrufe, keine Output-Dateien geschrieben.")
        return 0
    if not args.skip_discovery:
        discover_google_places(
            config.search_terms,
            tiles,
            raw_dir=args.raw_dir,
            checkpoint_path=args.google_checkpoint,
            resume=args.resume,
            limit_tiles=args.limit_tiles,
            smart_split=args.smart_split,
            split_min_new_place_ids=args.split_min_new_place_ids,
            split_min_new_ratio=args.split_min_new_ratio,
        )
    stats = process_raw_to_outputs(
        config,
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        final_dir=args.final_dir,
        reports_dir=args.reports_dir,
        enrich_email=not args.skip_email,
        contact_checkpoint_path=args.contact_checkpoint,
        contact_timeout=args.contact_timeout,
        contact_workers=args.contact_workers,
    )
    print("Stats:", stats)
    return 0


def main() -> int:
    try:
        return _main()
    except KeyboardInterrupt:
        print(
            "\nAbbruch erkannt. Fertige Discovery- und Contact-Schritte bleiben in den Checkpoints; "
            "finale Dateien werden nur nach vollstaendigem Schreiben ersetzt."
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
