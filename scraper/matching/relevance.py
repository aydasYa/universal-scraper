from __future__ import annotations

from typing import Any

from scraper.models import PlaceRecord

DEFAULT_POSITIVE_TERMS = {
    "hair_salon",
    "friseur",
    "friseursalon",
    "herrenfriseur",
    "damenfriseur",
    "barbershop",
    "barber",
    "coiffeur",
}
DEFAULT_UNCERTAIN_TERMS = {"beauty_salon", "spa", "kosmetik", "nails", "nagel", "wimpern"}
DEFAULT_NEGATIVE_TERMS = {"car_repair", "towing", "restaurant", "lodging", "dentist", "doctor", "real_estate_agency"}


def _term_set(config: Any | None, field_name: str, default_terms: set[str]) -> set[str]:
    if config is None:
        return {term.lower() for term in default_terms}
    values = getattr(config, field_name, [])
    return {str(term).lower() for term in values if str(term).strip()}


def _positive_terms(config: Any | None) -> set[str]:
    if config is None:
        return {term.lower() for term in DEFAULT_POSITIVE_TERMS}
    return {term.lower() for term in getattr(config, "effective_positive_terms", [])}


def score_relevance(record: PlaceRecord, config: Any | None = None) -> tuple[int, str, str]:
    haystack = " ".join(
        [
            record.firmenname,
            record.google_primary_type,
            record.google_types,
            record.gefunden_durch_suchbegriffe,
        ]
    ).lower()
    score = 0
    reasons: list[str] = []
    for term in _positive_terms(config):
        if term in haystack:
            score += 25 if term == "hair_salon" else 15
            reasons.append(f"positiv:{term}")
    for term in _term_set(config, "uncertain_terms", DEFAULT_UNCERTAIN_TERMS):
        if term in haystack:
            score -= 8
            reasons.append(f"unklar:{term}")
    for term in _term_set(config, "negative_terms", DEFAULT_NEGATIVE_TERMS):
        if term in haystack:
            score -= 50
            reasons.append(f"negativ:{term}")
    if record.business_status == "CLOSED_PERMANENTLY":
        score -= 100
        reasons.append("geschlossen")
    if not record.google_places_id or not record.firmenname:
        score -= 30
        reasons.append("ungueltige_kerndaten")
    if score >= 25:
        return score, "relevant", ", ".join(reasons)
    if score <= -25:
        return score, "irrelevant", ", ".join(reasons)
    return score, "unklar", ", ".join(reasons)


def classify_record(record: PlaceRecord, config: Any | None = None) -> PlaceRecord:
    score, status, reason = score_relevance(record, config)
    record.relevanz_score = score
    record.relevanz_status = status
    if record.business_status == "CLOSED_PERMANENTLY":
        record.klassifizierung = "aussortiert"
        record.klassifizierung_score = score
        record.klassifizierung_grund = "geschlossen"
        record.aussortiert_grund = "geschlossen"
        record.aussortiert_details = reason
    elif record.pruefgrund:
        record.klassifizierung = "manuelle_pruefung"
        record.klassifizierung_score = score
        record.klassifizierung_grund = record.pruefgrund
    elif status == "relevant":
        record.klassifizierung = "komplett"
        record.klassifizierung_score = score
        record.klassifizierung_grund = reason or "relevante_branchensignale"
    elif status == "irrelevant":
        record.klassifizierung = "aussortiert"
        record.klassifizierung_score = score
        record.klassifizierung_grund = reason or "irrelevant"
        record.aussortiert_grund = "irrelevant"
        record.aussortiert_details = reason
    else:
        record.klassifizierung = "manuelle_pruefung"
        record.klassifizierung_score = score
        record.klassifizierung_grund = reason or "unklare_branchenzuordnung"
        record.pruefgrund = record.pruefgrund or "unklare_branchenzuordnung"
        record.pruefhinweise = record.pruefhinweise or reason
    return record
