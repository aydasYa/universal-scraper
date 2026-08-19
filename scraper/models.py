from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PlaceRecord:
    firmenname: str = ""
    strasse: str = ""
    hausnummer: str = ""
    plz: str = ""
    ort: str = ""
    bundesland: str = ""
    telefon: str = ""
    telefon_international: str = ""
    website: str = ""
    website_quelle: str = ""
    email: str = ""
    email_quelle_url: str = ""
    email_typ: str = ""
    email_confidence: float | None = None
    google_places_id: str = ""
    google_maps_link: str = ""
    google_primary_type: str = ""
    google_types: str = ""
    business_status: str = ""
    breitengrad: float | None = None
    laengengrad: float | None = None
    erstfund_keyword: str = ""
    gefunden_durch_suchbegriffe: str = ""
    anzahl_suchbegriffe: int = 0
    quelle: str = "Google Places"
    relevanz_score: int = 0
    relevanz_status: str = ""
    klassifizierung: str = ""
    klassifizierung_score: int = 0
    klassifizierung_grund: str = ""
    pruefgrund: str = ""
    pruefhinweise: str = ""
    aussortiert_grund: str = ""
    aussortiert_details: str = ""
    duplikat_von: str = ""
    scrape_datum: str = field(default_factory=lambda: datetime.now().date().isoformat())
    raw_keywords: set[str] = field(default_factory=set)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_row(self, search_terms: list[str]) -> dict[str, Any]:
        data = self.__dict__.copy()
        raw_keywords = set(data.pop("raw_keywords", set()))
        data.pop("raw", None)
        ordered = [term for term in search_terms if term in raw_keywords]
        data["gefunden_durch_suchbegriffe"] = ", ".join(ordered)
        data["anzahl_suchbegriffe"] = len(ordered)
        for term in search_terms:
            data["kw_" + term.lower().replace(" ", "_").replace("-", "_")] = term in raw_keywords
        return data

