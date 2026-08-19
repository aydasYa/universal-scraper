from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

from scraper.storage import append_jsonl, atomic_write_lines

LOGGER = logging.getLogger(__name__)

TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
TEXT_SEARCH_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.name",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.googleMapsUri",
        "places.primaryType",
        "places.types",
        "places.businessStatus",
        "places.location",
        "nextPageToken",
    ]
)


@dataclass(frozen=True)
class Tile:
    south: float
    west: float
    north: float
    east: float
    depth: int = 0

    @property
    def id(self) -> str:
        raw = f"{self.south:.5f},{self.west:.5f},{self.north:.5f},{self.east:.5f},d{self.depth}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    @property
    def center(self) -> tuple[float, float]:
        return ((self.south + self.north) / 2, (self.west + self.east) / 2)

    @property
    def radius_m(self) -> int:
        lat_km = max(1.0, (self.north - self.south) * 111.0)
        lon_km = max(1.0, (self.east - self.west) * 72.0)
        return min(50000, int(max(lat_km, lon_km) * 650))

    def split(self) -> list["Tile"]:
        mid_lat = (self.south + self.north) / 2
        mid_lon = (self.west + self.east) / 2
        depth = self.depth + 1
        return [
            Tile(self.south, self.west, mid_lat, mid_lon, depth),
            Tile(self.south, mid_lon, mid_lat, self.east, depth),
            Tile(mid_lat, self.west, self.north, mid_lon, depth),
            Tile(mid_lat, mid_lon, self.north, self.east, depth),
        ]


def germany_tiles(step_degrees: float = 1.0, overlap_degrees: float = 0.08) -> list[Tile]:
    tiles: list[Tile] = []
    south, north = 47.2, 55.1
    west, east = 5.7, 15.2
    lat = south
    while lat < north:
        lon = west
        while lon < east:
            tiles.append(
                Tile(
                    max(south, lat - overlap_degrees),
                    max(west, lon - overlap_degrees),
                    min(north, lat + step_degrees + overlap_degrees),
                    min(east, lon + step_degrees + overlap_degrees),
                )
            )
            lon += step_degrees
        lat += step_degrees
    return tiles


def berlin_test_tiles() -> list[Tile]:
    return [Tile(52.43, 13.28, 52.57, 13.53)]


def _raw_file_for(raw_path: Path, keyword: str, tile: Tile) -> Path:
    return raw_path / f"{keyword.lower()}_{tile.id}.jsonl"


def _place_id_from_raw(raw: dict[str, Any]) -> str:
    place = raw.get("details") or raw.get("search_result") or {}
    return place.get("id") or place.get("place_id") or ""


def _read_raw_place_ids(path: Path) -> set[str]:
    place_ids: set[str] = set()
    if not path.exists():
        return place_ids
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                LOGGER.warning("skipping invalid raw JSONL line file=%s line=%s error=%s", path, line_number, exc)
                continue
            place_id = _place_id_from_raw(raw)
            if place_id:
                place_ids.add(place_id)
    return place_ids


class CheckpointStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        LOGGER.warning(
                            "skipping invalid discovery checkpoint line file=%s line=%s error=%s",
                            self.path,
                            line_number,
                            exc,
                        )
                        continue
                    key = record.get("key")
                    if key:
                        self.records[key] = record

    @staticmethod
    def make_key(keyword: str, tile: Tile) -> str:
        return f"{keyword}|{tile.id}"

    def is_done(self, keyword: str, tile: Tile) -> bool:
        record = self.records.get(self.make_key(keyword, tile))
        return bool(record and record.get("status") == "done")

    def get(self, keyword: str, tile: Tile) -> dict[str, Any] | None:
        return self.records.get(self.make_key(keyword, tile))

    def write(self, keyword: str, tile: Tile, status: str, **extra: Any) -> None:
        record = {
            "key": self.make_key(keyword, tile),
            "keyword": keyword,
            "tile_id": tile.id,
            "tile": asdict(tile),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        self.records[record["key"]] = record
        append_jsonl(self.path, record)


class GooglePlacesClient:
    def __init__(self, api_key: str | None = None, timeout: int = 20, max_retries: int = 3):
        self.api_key = api_key or os.getenv("PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("PLACES_API_KEY is required for live Google Places discovery.")
        self.timeout = timeout
        self.max_retries = max_retries

    def _post(self, url: str, payload: dict[str, Any], field_mask: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise
            if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries - 1:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                message = data["error"].get("message", "")
                code = data["error"].get("code", "")
                if code in {429, 500, 503} and attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"Google Places API (New) error: {code} {message}")
            return data
        raise RuntimeError(f"Google Places API retry loop exhausted: {last_error}")

    def text_search(self, keyword: str, tile: Tile) -> list[dict[str, Any]]:
        lat, lon = tile.center
        payload: dict[str, Any] = {
            "textQuery": keyword,
            "languageCode": "de",
            "regionCode": "DE",
            "pageSize": 20,
            "includePureServiceAreaBusinesses": False,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": float(tile.radius_m),
                }
            },
        }
        places: list[dict[str, Any]] = []
        while True:
            data = self._post(TEXT_SEARCH_URL, payload, TEXT_SEARCH_FIELD_MASK)
            places.extend(data.get("places", []))
            token = data.get("nextPageToken")
            if not token:
                return places
            LOGGER.info("pagination keyword=%s tile=%s total=%s", keyword, tile.id, len(places))
            payload = {**payload, "pageToken": token}


def discover_google_places(
    search_terms: Iterable[str],
    tiles: Iterable[Tile],
    raw_dir: str | Path = "data/raw/google_places",
    checkpoint_path: str | Path = "data/checkpoints/google_places.jsonl",
    resume: bool = True,
    limit_tiles: int | None = None,
    max_split_depth: int = 3,
    dense_threshold: int = 55,
    smart_split: bool = True,
    split_min_new_place_ids: int = 8,
    split_min_new_ratio: float = 0.15,
    client: GooglePlacesClient | None = None,
) -> list[dict[str, Any]]:
    client = client or GooglePlacesClient()
    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    checkpoints = CheckpointStore(checkpoint_path)
    all_results: list[dict[str, Any]] = []
    seen_place_ids: set[str] = set()
    base_tiles = list(tiles)
    if limit_tiles is not None:
        base_tiles = base_tiles[:limit_tiles]

    for keyword in search_terms:
        keyword_seen_place_ids: set[str] = set()
        queue = list(base_tiles)
        while queue:
            tile = queue.pop(0)
            checkpoint = checkpoints.get(keyword, tile)
            if resume and checkpoint and checkpoint.get("status") == "done":
                skipped_place_ids = _read_raw_place_ids(_raw_file_for(raw_path, keyword, tile))
                keyword_seen_place_ids.update(skipped_place_ids)
                seen_place_ids.update(skipped_place_ids)
                LOGGER.info("checkpoint skip keyword=%s tile=%s", keyword, tile.id)
                if checkpoint.get("split") and tile.depth < max_split_depth:
                    queue.extend(tile.split())
                continue
            LOGGER.info("discover keyword=%s tile=%s depth=%s", keyword, tile.id, tile.depth)
            checkpoints.write(keyword, tile, "started")
            try:
                results = client.text_search(keyword, tile)
                place_ids = [place.get("id") for place in results if place.get("id")]
                keyword_new_ids = [place_id for place_id in place_ids if place_id not in keyword_seen_place_ids]
                keyword_known_ids = len(place_ids) - len(keyword_new_ids)
                global_new_ids = [place_id for place_id in place_ids if place_id not in seen_place_ids]
                global_known_ids = len(place_ids) - len(global_new_ids)
                keyword_seen_place_ids.update(place_ids)
                seen_place_ids.update(place_ids)
                LOGGER.info(
                    "result keyword=%s tile=%s treffer=%s keyword_neu=%s keyword_bekannt=%s global_neu=%s global_bekannt=%s gesamt_eindeutig=%s",
                    keyword,
                    tile.id,
                    len(results),
                    len(keyword_new_ids),
                    keyword_known_ids,
                    len(global_new_ids),
                    global_known_ids,
                    len(seen_place_ids),
                )
                enriched: list[dict[str, Any]] = []
                for place in results:
                    enriched.append({"keyword": keyword, "tile": asdict(tile), "search_result": place, "details": place})
                raw_file = _raw_file_for(raw_path, keyword, tile)
                atomic_write_lines(
                    raw_file,
                    (json.dumps(record, ensure_ascii=False) + "\n" for record in enriched),
                )
                all_results.extend(enriched)
                split = len(results) >= dense_threshold and tile.depth < max_split_depth
                if smart_split and split and tile.depth > 0:
                    unique_place_ids = set(place_ids)
                    keyword_new_unique_ids = set(keyword_new_ids)
                    new_ratio = len(keyword_new_unique_ids) / len(unique_place_ids) if unique_place_ids else 0.0
                    split = len(keyword_new_unique_ids) >= split_min_new_place_ids or new_ratio >= split_min_new_ratio
                    if not split:
                        LOGGER.info(
                            "smart split stop keyword=%s tile=%s depth=%s unique=%s keyword_new_unique=%s new_ratio=%.2f min_new=%s min_ratio=%.2f",
                            keyword,
                            tile.id,
                            tile.depth,
                            len(unique_place_ids),
                            len(keyword_new_unique_ids),
                            new_ratio,
                            split_min_new_place_ids,
                            split_min_new_ratio,
                        )
                checkpoints.write(keyword, tile, "done", result_count=len(results), split=split)
                LOGGER.info("checkpoint done keyword=%s tile=%s split=%s", keyword, tile.id, split)
                if split:
                    LOGGER.info("split keyword=%s tile=%s count=%s", keyword, tile.id, len(results))
                    queue.extend(tile.split())
            except Exception as exc:
                LOGGER.warning("discovery failed keyword=%s tile=%s error=%s", keyword, tile.id, exc)
                checkpoints.write(keyword, tile, "error", error=str(exc))
    return all_results


def read_raw_google_places(raw_dir: str | Path = "data/raw/google_places") -> list[dict[str, Any]]:
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
