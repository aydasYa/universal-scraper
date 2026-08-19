from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class BranchConfig:
    slug: str
    name: str
    search_terms: list[str]

    @property
    def keyword_columns(self) -> dict[str, str]:
        return {term: "kw_" + term.lower().replace(" ", "_").replace("-", "_") for term in self.search_terms}


def load_config(path: str | Path = "config/friseure.yaml") -> BranchConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    terms = data.get("search_terms") or []
    if not terms:
        raise ValueError("Config must define at least one search term.")
    return BranchConfig(slug=data["slug"], name=data["name"], search_terms=list(terms))
