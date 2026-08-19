from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scraper.matching.normalize import normalize_url
from scraper.models import PlaceRecord
from scraper.storage import append_jsonl

LOGGER = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.+-])", re.I)
PREFERRED_PREFIXES = ("info@", "kontakt@", "office@", "hallo@", "hello@", "termin@", "service@")
LOW_PRIORITY_PREFIXES = ("datenschutz@", "privacy@", "presse@", "bewerbung@")
CONTACT_PATHS = ["", "kontakt", "kontakt/", "impressum", "impressum/", "ueber-uns", "about", "contact"]
DEFAULT_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class EmailCandidate:
    email: str
    source_url: str
    confidence: float
    email_type: str


class ContactCheckpointStore:
    def __init__(self, path: str | Path = "data/checkpoints/contact_enrichment.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, dict] = {}
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        LOGGER.warning(
                            "skipping invalid contact checkpoint line file=%s line=%s error=%s",
                            self.path,
                            line_number,
                            exc,
                        )
                        continue
                    website = self._key(record.get("website", ""))
                    if website:
                        self.records[website] = record

    @staticmethod
    def _key(website: str) -> str:
        return normalize_url(website)

    def get_done(self, website: str) -> dict | None:
        record = self.records.get(self._key(website))
        if record and record.get("status") == "done":
            return record
        return None

    def write(self, website: str, candidate: EmailCandidate | None, status: str, **extra: object) -> None:
        normalized_website = self._key(website)
        record = {
            "website": normalized_website,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "email": candidate.email if candidate else "",
            "source_url": candidate.source_url if candidate else "",
            "confidence": candidate.confidence if candidate else None,
            "email_type": candidate.email_type if candidate else "",
            **extra,
        }
        self.records[normalized_website] = record
        append_jsonl(self.path, record)


def _fetch(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS, session: requests.Session | None = None) -> str:
    requester = session or requests
    response = requester.get(url, timeout=timeout, headers={"User-Agent": "FriseurScraper/1.0"})
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        return ""
    return response.text


def _candidate_score(email: str) -> tuple[float, str]:
    lower = email.lower()
    if lower.startswith(PREFERRED_PREFIXES):
        return 0.9, "allgemein"
    if lower.startswith(LOW_PRIORITY_PREFIXES):
        return 0.35, "niedrig_priorisiert"
    return 0.65, "unklar"


def extract_emails(html: str, source_url: str) -> list[EmailCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ")
    mailtos = [link.get("href", "")[7:].split("?", 1)[0] for link in soup.select('a[href^="mailto:"]')]
    emails = set(mailtos)
    emails.update(match.group(1) for match in EMAIL_RE.finditer(text))
    candidates: list[EmailCandidate] = []
    for email in emails:
        normalized = email.strip().lower()
        if not normalized:
            continue
        confidence, email_type = _candidate_score(normalized)
        candidates.append(EmailCandidate(normalized, source_url, confidence, email_type))
    return sorted(candidates, key=lambda item: item.confidence, reverse=True)


def find_contact_email(website: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> EmailCandidate | None:
    website = normalize_url(website)
    if not website:
        return None
    with requests.Session() as session:
        for path in CONTACT_PATHS:
            url = urljoin(website.rstrip("/") + "/", path)
            try:
                html = _fetch(url, timeout=timeout, session=session)
            except Exception as exc:
                LOGGER.debug("contact fetch failed url=%s error=%s", url, exc)
                continue
            candidates = extract_emails(html, url)
            if candidates:
                return candidates[0]
    return None


def _apply_checkpoint(record: PlaceRecord, cached: dict) -> None:
    if cached.get("email"):
        record.email = cached["email"]
        record.email_quelle_url = cached.get("source_url", "")
        record.email_typ = cached.get("email_type", "")
        record.email_confidence = cached.get("confidence")


def _apply_candidate(record: PlaceRecord, candidate: EmailCandidate | None) -> None:
    if not candidate:
        return
    record.email = candidate.email
    record.email_quelle_url = candidate.source_url
    record.email_typ = candidate.email_type
    record.email_confidence = candidate.confidence


def enrich_contacts(
    records: list[PlaceRecord],
    checkpoint_path: str | Path = "data/checkpoints/contact_enrichment.jsonl",
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_workers: int = 4,
) -> None:
    checkpoints = ContactCheckpointStore(checkpoint_path)
    pending: dict[str, list[tuple[int, PlaceRecord]]] = defaultdict(list)
    for index, record in enumerate(records, start=1):
        if not record.website or record.email:
            continue
        website = normalize_url(record.website)
        if not website:
            continue
        cached = checkpoints.get_done(website)
        if cached:
            _apply_checkpoint(record, cached)
            LOGGER.info(
                "contact checkpoint skip %s/%s website=%s email=%s",
                index,
                len(records),
                website,
                "yes" if cached.get("email") else "no",
            )
            continue
        pending[website].append((index, record))

    if not pending:
        return

    max_workers = max(1, min(max_workers, len(pending)))
    pending_records = sum(len(group) for group in pending.values())
    LOGGER.info(
        "contact enrichment pending websites=%s records=%s workers=%s timeout=%ss",
        len(pending),
        pending_records,
        max_workers,
        timeout,
    )

    def finish_website(done_count: int, website: str, candidate: EmailCandidate | None) -> None:
        for _, record in pending[website]:
            _apply_candidate(record, candidate)
        checkpoints.write(website, candidate, "done")
        LOGGER.info(
            "contact checkpoint done website=%s/%s records=%s url=%s email=%s",
            done_count,
            len(pending),
            len(pending[website]),
            website,
            candidate.email if candidate else "none",
        )

    if max_workers == 1:
        for done_count, website in enumerate(pending, start=1):
            LOGGER.info("contact enrichment website=%s/%s url=%s", done_count, len(pending), website)
            finish_website(done_count, website, find_contact_email(website, timeout=timeout))
        return

    executor = ThreadPoolExecutor(max_workers=max_workers)
    try:
        future_to_website = {
            executor.submit(find_contact_email, website, timeout=timeout): website
            for website in pending
        }
        for done_count, future in enumerate(as_completed(future_to_website), start=1):
            website = future_to_website[future]
            try:
                candidate = future.result()
            except Exception as exc:
                LOGGER.warning("contact enrichment failed url=%s error=%s", website, exc)
                checkpoints.write(website, None, "error", error=str(exc))
                continue
            finish_website(done_count, website, candidate)
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)
