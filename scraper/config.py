from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@dataclass(frozen=True)
class BranchConfig:
    slug: str
    name: str
    search_terms: list[str]
    category: str = ""
    google_included_type: str = ""
    positive_terms: list[str] = field(default_factory=list)
    uncertain_terms: list[str] = field(default_factory=list)
    negative_terms: list[str] = field(default_factory=list)

    @property
    def data_dir(self) -> Path:
        return Path("data") / "projects" / self.slug

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw" / "google_places"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def final_dir(self) -> Path:
        return self.data_dir / "final"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def google_checkpoint_path(self) -> Path:
        return self.data_dir / "checkpoints" / "google_places.jsonl"

    @property
    def contact_checkpoint_path(self) -> Path:
        return self.data_dir / "checkpoints" / "contact_enrichment.jsonl"

    @property
    def keyword_columns(self) -> dict[str, str]:
        return {term: "kw_" + term.lower().replace(" ", "_").replace("-", "_") for term in self.search_terms}

    @property
    def effective_positive_terms(self) -> list[str]:
        if self.positive_terms:
            return self.positive_terms
        terms = list(self.search_terms)
        if self.google_included_type:
            terms.append(self.google_included_type)
        return terms


def _list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        raise ValueError("Config project.slug may only contain lowercase letters, numbers, '_' and '-'.")


def _load_modern_config(data: dict[str, Any]) -> BranchConfig:
    project = data.get("project") or {}
    search = data.get("search") or {}
    google = data.get("google") or {}
    relevance = data.get("relevance") or {}
    terms = _list(search.get("terms"))
    if not terms:
        raise ValueError("Config must define at least one search term in search.terms.")
    slug = str(project.get("slug") or "").strip()
    name = str(project.get("name") or "").strip()
    if not slug:
        raise ValueError("Config must define project.slug.")
    _validate_slug(slug)
    if not name:
        raise ValueError("Config must define project.name.")
    return BranchConfig(
        slug=slug,
        name=name,
        category=str(project.get("category") or "").strip(),
        search_terms=terms,
        google_included_type=str(google.get("included_type") or "").strip(),
        positive_terms=_list(relevance.get("positive_terms")),
        uncertain_terms=_list(relevance.get("uncertain_terms")),
        negative_terms=_list(relevance.get("negative_terms")),
    )


def _load_legacy_config(data: dict[str, Any]) -> BranchConfig:
    terms = _list(data.get("search_terms"))
    if not terms:
        raise ValueError("Config must define at least one search term.")
    _validate_slug(str(data["slug"]))
    return BranchConfig(
        slug=str(data["slug"]),
        name=str(data["name"]),
        search_terms=terms,
    )


def load_config(path: str | Path = "config/active.yaml") -> BranchConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if "project" in data or "search" in data:
        return _load_modern_config(data)
    return _load_legacy_config(data)
