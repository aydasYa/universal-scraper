from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scraper.config import BranchConfig
from scraper.enrichment.contacts import enrich_contacts
from scraper.export.xlsx import export_final_workbooks, export_keyword_statistics
from scraper.matching.deduplicate import deduplicate_records
from scraper.matching.relevance import classify_record
from scraper.models import PlaceRecord
from scraper.storage import atomic_write_lines

LOGGER = logging.getLogger(__name__)


def _component(details: dict[str, Any], kind: str) -> str:
    for component in details.get("addressComponents", details.get("address_components", [])):
        if kind in component.get("types", []):
            return component.get("longText") or component.get("long_name", "")
    return ""


def _display_name(place: dict[str, Any]) -> str:
    display_name = place.get("displayName")
    if isinstance(display_name, dict):
        return display_name.get("text", "")
    return place.get("name", "")


def _place_id(place: dict[str, Any]) -> str:
    return place.get("id") or place.get("place_id", "")


def record_from_google_raw(raw: dict[str, Any]) -> PlaceRecord:
    details = raw.get("details") or raw.get("search_result") or {}
    search_result = raw.get("search_result") or {}
    location = details.get("location") or search_result.get("location")
    if not location:
        geometry = details.get("geometry") or search_result.get("geometry") or {}
        location = geometry.get("location") or {}
    types = details.get("types") or search_result.get("types") or []
    address = details.get("formattedAddress") or search_result.get("formattedAddress")
    address = address or details.get("formatted_address") or search_result.get("formatted_address") or ""
    from scraper.matching.normalize import split_street_house

    strasse, hausnummer = split_street_house(address)
    website = details.get("websiteUri") or details.get("website", "") or ""
    keyword = raw.get("keyword", "")
    return PlaceRecord(
        firmenname=_display_name(details) or _display_name(search_result),
        strasse=strasse,
        hausnummer=hausnummer,
        plz=_component(details, "postal_code"),
        ort=_component(details, "locality") or _component(details, "postal_town"),
        bundesland=_component(details, "administrative_area_level_1"),
        telefon=details.get("nationalPhoneNumber") or details.get("formatted_phone_number", ""),
        telefon_international=details.get("internationalPhoneNumber") or details.get("international_phone_number", ""),
        website=website,
        website_quelle="Google Places" if website else "",
        google_places_id=_place_id(details) or _place_id(search_result),
        google_maps_link=details.get("googleMapsUri") or details.get("url", ""),
        google_primary_type=details.get("primaryType") or (types[0] if types else ""),
        google_types=", ".join(types),
        business_status=details.get("businessStatus") or details.get("business_status") or search_result.get("business_status", ""),
        breitengrad=location.get("latitude", location.get("lat")),
        laengengrad=location.get("longitude", location.get("lng")),
        erstfund_keyword=keyword,
        raw_keywords={keyword} if keyword else set(),
        raw=raw,
    )


def load_raw_records(raw_dir: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    path = Path(raw_dir)
    if not path.exists():
        return records
    for file in sorted(path.glob("*.jsonl")):
        with file.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    LOGGER.warning("skipping invalid raw JSONL line file=%s line=%s error=%s", file, line_number, exc)
    return records


def build_keyword_statistics(raw_records: list[dict[str, Any]], config: BranchConfig) -> list[dict[str, Any]]:
    keyword_to_place_ids: dict[str, set[str]] = defaultdict(set)
    raw_counts = Counter()
    place_to_keywords: dict[str, set[str]] = defaultdict(set)
    for raw in raw_records:
        keyword = raw.get("keyword", "")
        place = raw.get("details") or raw.get("search_result") or {}
        place_id = _place_id(place) or _place_id(raw.get("search_result") or {})
        if not keyword:
            continue
        raw_counts[keyword] += 1
        if place_id:
            keyword_to_place_ids[keyword].add(place_id)
            place_to_keywords[place_id].add(keyword)
    rows = []
    for keyword in config.search_terms:
        place_ids = keyword_to_place_ids[keyword]
        exclusive = {pid for pid in place_ids if place_to_keywords[pid] == {keyword}}
        overlapping_place_ids = {pid for pid in place_ids if len(place_to_keywords[pid]) > 1}
        also = len(overlapping_place_ids)
        overlap_counts = {
            other: sum(1 for pid in place_ids if other != keyword and other in place_to_keywords[pid])
            for other in config.search_terms
        }
        overlap_details = "; ".join([f"{other}: {count}" for other, count in overlap_counts.items() if count])
        combination_counts = Counter(
            " + ".join([term for term in config.search_terms if term in place_to_keywords[pid]])
            for pid in overlapping_place_ids
        )
        combination_details = "; ".join(
            [f"{combination}: {count}" for combination, count in sorted(combination_counts.items())]
        )
        overlap_columns = {
            "auch_kw_" + other.lower().replace(" ", "_").replace("-", "_"): count
            for other, count in overlap_counts.items()
        }
        rows.append(
            {
                "suchbegriff": keyword,
                "rohtreffer": raw_counts[keyword],
                "eindeutige_place_ids": len(place_ids),
                "exklusive_place_ids": len(exclusive),
                "auch_ueber_andere_keywords": also,
                "auch_ueber_andere_keywords_details": overlap_details,
                "keyword_kombinationen_details": combination_details,
                "anteil_exklusiv_prozent": round((len(exclusive) / len(place_ids) * 100) if place_ids else 0, 2),
                **overlap_columns,
            }
        )
    return rows


def process_raw_to_outputs(
    config: BranchConfig,
    raw_dir: str | Path = "data/raw/google_places",
    processed_dir: str | Path = "data/processed",
    final_dir: str | Path = "data/final",
    reports_dir: str | Path = "data/reports",
    enrich_email: bool = True,
    contact_checkpoint_path: str | Path = "data/checkpoints/contact_enrichment.jsonl",
    contact_timeout: int = 5,
    contact_workers: int = 4,
) -> dict[str, int]:
    LOGGER.info("loading raw Google Places records from %s", raw_dir)
    raw_records = load_raw_records(raw_dir)
    LOGGER.info("loaded %s raw records", len(raw_records))
    records = [record_from_google_raw(raw) for raw in raw_records]
    LOGGER.info("deduplicating records")
    deduped, discarded_duplicates = deduplicate_records(records, config.search_terms)
    LOGGER.info("deduplicated to %s records, discarded %s duplicates", len(deduped), len(discarded_duplicates))
    if enrich_email:
        LOGGER.info("starting contact enrichment for records with websites")
        enrich_contacts(
            deduped,
            checkpoint_path=contact_checkpoint_path,
            timeout=contact_timeout,
            max_workers=contact_workers,
        )
        LOGGER.info("finished contact enrichment")
    komplett: list[PlaceRecord] = []
    manuell: list[PlaceRecord] = []
    aussortiert: list[PlaceRecord] = list(discarded_duplicates)
    for record in deduped:
        classify_record(record, config)
        if record.klassifizierung == "komplett":
            komplett.append(record)
        elif record.klassifizierung == "manuelle_pruefung":
            manuell.append(record)
        else:
            aussortiert.append(record)

    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    processed_file = Path(processed_dir) / "standorte.jsonl"
    LOGGER.info("writing processed records to %s", processed_file)
    atomic_write_lines(
        processed_file,
        (
            json.dumps(record.to_row(config.search_terms), ensure_ascii=False, default=str) + "\n"
            for record in deduped
        ),
    )

    LOGGER.info("exporting final workbooks to %s", final_dir)
    export_final_workbooks(komplett, manuell, aussortiert, config.search_terms, final_dir)
    LOGGER.info("exporting keyword statistics to %s", reports_dir)
    export_keyword_statistics(
        build_keyword_statistics(raw_records, config),
        Path(reports_dir) / "keyword_statistik.xlsx",
        config.search_terms,
    )
    stats = {
        "rohtreffer": len(raw_records),
        "eindeutige_place_ids": len({r.google_places_id for r in deduped if r.google_places_id}),
        "komplett": len(komplett),
        "manuelle_pruefung": len(manuell),
        "aussortiert": len(aussortiert),
        "mit_website": sum(1 for r in deduped if r.website),
        "mit_email": sum(1 for r in deduped if r.email),
    }
    LOGGER.info("pipeline stats=%s", stats)
    return stats
