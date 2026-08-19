from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher

from scraper.matching.normalize import normalize_name, normalize_phone
from scraper.models import PlaceRecord

_LAT_BUCKET_SIZE = 0.00015
_LNG_BUCKET_SIZE = 0.00025


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _address_key(record: PlaceRecord) -> tuple[str, str, str, str]:
    return (record.strasse, record.hausnummer, record.plz, record.ort.lower())


def _address_is_specific(address: tuple[str, str, str, str]) -> bool:
    return bool(address[0] and address[1] and (address[2] or address[3]))


def _phone_key(record: PlaceRecord) -> str:
    return normalize_phone(record.telefon_international or record.telefon)


def _coord_bucket(record: PlaceRecord) -> tuple[str, int, int] | None:
    if record.breitengrad is None or record.laengengrad is None:
        return None
    return (
        record.plz,
        int(record.breitengrad / _LAT_BUCKET_SIZE),
        int(record.laengengrad / _LNG_BUCKET_SIZE),
    )


def _nearby_coord_buckets(record: PlaceRecord) -> list[tuple[str, int, int]]:
    bucket = _coord_bucket(record)
    if bucket is None:
        return []
    plz, lat_bucket, lng_bucket = bucket
    return [
        (plz, lat_bucket + lat_offset, lng_bucket + lng_offset)
        for lat_offset in range(-1, 2)
        for lng_offset in range(-1, 2)
    ]


def merge_records(primary: PlaceRecord, other: PlaceRecord, search_terms: list[str]) -> PlaceRecord:
    if not primary.erstfund_keyword:
        primary.erstfund_keyword = other.erstfund_keyword
    primary.raw_keywords.update(other.raw_keywords)
    for field in [
        "firmenname",
        "strasse",
        "hausnummer",
        "plz",
        "ort",
        "bundesland",
        "telefon",
        "telefon_international",
        "website",
        "website_quelle",
        "google_maps_link",
        "google_primary_type",
        "google_types",
        "business_status",
    ]:
        if not getattr(primary, field) and getattr(other, field):
            setattr(primary, field, getattr(other, field))
    if primary.breitengrad is None:
        primary.breitengrad = other.breitengrad
    if primary.laengengrad is None:
        primary.laengengrad = other.laengengrad
    primary.gefunden_durch_suchbegriffe = ", ".join([term for term in search_terms if term in primary.raw_keywords])
    primary.anzahl_suchbegriffe = len(primary.raw_keywords)
    return primary


def is_strong_same_location(a: PlaceRecord, b: PlaceRecord) -> bool:
    same_address = all(_address_key(a)) and _address_key(a) == _address_key(b)
    name_close = _similar(normalize_name(a.firmenname), normalize_name(b.firmenname)) >= 0.86
    if same_address and name_close:
        return True
    phone_a = normalize_phone(a.telefon_international or a.telefon)
    phone_b = normalize_phone(b.telefon_international or b.telefon)
    if phone_a and phone_a == phone_b and same_address:
        return True
    if a.breitengrad is not None and b.breitengrad is not None and a.laengengrad is not None and b.laengengrad is not None:
        very_close = abs(a.breitengrad - b.breitengrad) < 0.00015 and abs(a.laengengrad - b.laengengrad) < 0.00025
        if very_close and name_close and (a.plz == b.plz or same_address):
            return True
    return False


def maybe_duplicate(a: PlaceRecord, b: PlaceRecord) -> bool:
    address = _address_key(a)
    same_address = address == _address_key(b) and _address_is_specific(address)
    name_somewhat_close = _similar(normalize_name(a.firmenname), normalize_name(b.firmenname)) >= 0.68
    phone_a = normalize_phone(a.telefon_international or a.telefon)
    phone_b = normalize_phone(b.telefon_international or b.telefon)
    same_phone = bool(phone_a and phone_a == phone_b)
    return (same_address and name_somewhat_close) or (same_phone and name_somewhat_close)


def deduplicate_records(records: list[PlaceRecord], search_terms: list[str]) -> tuple[list[PlaceRecord], list[PlaceRecord]]:
    kept: list[PlaceRecord] = []
    discarded: list[PlaceRecord] = []
    by_place_id: dict[str, PlaceRecord] = {}
    kept_indexes: dict[int, int] = {}
    by_address: dict[tuple[str, str, str, str], list[PlaceRecord]] = defaultdict(list)
    by_phone: dict[str, list[PlaceRecord]] = defaultdict(list)
    by_coord_bucket: dict[tuple[str, int, int], list[PlaceRecord]] = defaultdict(list)
    indexed_addresses: dict[int, set[tuple[str, str, str, str]]] = defaultdict(set)
    indexed_phones: dict[int, set[str]] = defaultdict(set)
    indexed_coord_buckets: dict[int, set[tuple[str, int, int]]] = defaultdict(set)

    def add_to_indexes(record: PlaceRecord, index: int | None = None) -> None:
        record_id = id(record)
        kept_indexes[record_id] = len(kept) - 1 if index is None else index
        address = _address_key(record)
        if _address_is_specific(address) and address not in indexed_addresses[record_id]:
            by_address[address].append(record)
            indexed_addresses[record_id].add(address)
        phone = _phone_key(record)
        if phone and phone not in indexed_phones[record_id]:
            by_phone[phone].append(record)
            indexed_phones[record_id].add(phone)
        bucket = _coord_bucket(record)
        if bucket is not None and bucket not in indexed_coord_buckets[record_id]:
            by_coord_bucket[bucket].append(record)
            indexed_coord_buckets[record_id].add(bucket)

    def candidate_records(record: PlaceRecord) -> list[PlaceRecord]:
        candidates: dict[int, PlaceRecord] = {}
        address = _address_key(record)
        if _address_is_specific(address):
            for existing in by_address.get(address, []):
                candidates[id(existing)] = existing
        phone = _phone_key(record)
        if phone:
            for existing in by_phone.get(phone, []):
                candidates[id(existing)] = existing
        for bucket in _nearby_coord_buckets(record):
            for existing in by_coord_bucket.get(bucket, []):
                candidates[id(existing)] = existing
        return sorted(candidates.values(), key=lambda item: kept_indexes[id(item)])

    for record in records:
        if record.google_places_id and record.google_places_id in by_place_id:
            kept_record = by_place_id[record.google_places_id]
            merge_records(kept_record, record, search_terms)
            add_to_indexes(kept_record, kept_indexes[id(kept_record)])
            duplicate = record
            duplicate.klassifizierung = "aussortiert"
            duplicate.aussortiert_grund = "duplikat"
            duplicate.aussortiert_details = "Gleiche Google Place ID"
            duplicate.duplikat_von = kept_record.google_places_id
            discarded.append(duplicate)
            continue

        merged = False
        for existing in candidate_records(record):
            if is_strong_same_location(existing, record):
                merge_records(existing, record, search_terms)
                add_to_indexes(existing, kept_indexes[id(existing)])
                record.klassifizierung = "aussortiert"
                record.aussortiert_grund = "duplikat"
                record.aussortiert_details = "Starke Name/Adresse/Telefon/Koordinaten-Übereinstimmung"
                record.duplikat_von = existing.google_places_id or existing.firmenname
                discarded.append(record)
                merged = True
                break
            if maybe_duplicate(existing, record):
                existing.pruefgrund = existing.pruefgrund or "moegliches_duplikat"
                existing.pruefhinweise = "Aehnliche Standortsignale mit anderer Place ID"
                record.pruefgrund = record.pruefgrund or "moegliches_duplikat"
                record.pruefhinweise = "Aehnliche Standortsignale mit anderer Place ID"
        if not merged:
            kept.append(record)
            add_to_indexes(record)
            if record.google_places_id:
                by_place_id[record.google_places_id] = record
    for record in kept:
        record.gefunden_durch_suchbegriffe = ", ".join([term for term in search_terms if term in record.raw_keywords])
        record.anzahl_suchbegriffe = len(record.raw_keywords)
    return kept, discarded
