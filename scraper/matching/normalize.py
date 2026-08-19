from __future__ import annotations

import re
from urllib.parse import urlparse


def normalize_name(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"\b(gmbh|ug|kg|ohg|inh\.?|friseursalon|friseur|hair|salon)\b", " ", text)
    text = re.sub(r"[^a-z0-9äöüß]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_street_house(address: str | None) -> tuple[str, str]:
    first = (address or "").split(",", 1)[0].strip()
    match = re.match(r"^(.*?)(\d+[a-zA-Z]?(?:\s?-\s?\d+[a-zA-Z]?)?)$", first)
    if not match:
        return normalize_street(first), ""
    return normalize_street(match.group(1)), match.group(2).replace(" ", "")


def normalize_street(value: str | None) -> str:
    text = (value or "").lower().strip()
    text = text.replace("straße", "str").replace("str.", "str")
    text = re.sub(r"[^a-z0-9äöüß]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_postcode(value: str | None) -> str:
    match = re.search(r"\b(\d{5})\b", value or "")
    return match.group(1) if match else ""


def normalize_city(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"[^a-zäöüß]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_phone(value: str | None) -> str:
    raw = value or ""
    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return ""
    if digits.startswith("0049"):
        return "+49" + digits[4:]
    if digits.startswith("49"):
        return "+49" + digits[2:]
    if digits.startswith("0"):
        return "+49" + digits[1:]
    if raw.strip().startswith("+"):
        return "+" + digits
    return digits


def normalize_url(value: str | None) -> str:
    if not value:
        return ""
    url = value.strip()
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{host}{path}"


def normalize_domain(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(normalize_url(value))
    return parsed.netloc.lower().removeprefix("www.")


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()
