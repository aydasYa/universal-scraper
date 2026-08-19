from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkuPrice:
    name: str
    free_cap: int
    usd_per_1000: float


TEXT_SEARCH_NEW_ENTERPRISE = SkuPrice("Places API Text Search Enterprise (New)", 1000, 35.0)


def billable_cost_usd(requests: int, price: SkuPrice) -> float:
    billable = max(0, requests - price.free_cap)
    return billable / 1000 * price.usd_per_1000


def estimate_google_places_cost(
    text_search_requests: int,
    details_requests: int = 0,
    include_monthly_free_cap: bool = True,
) -> dict[str, float | int | str]:
    text_price = TEXT_SEARCH_NEW_ENTERPRISE
    if include_monthly_free_cap:
        text_cost = billable_cost_usd(text_search_requests, text_price)
    else:
        text_cost = text_search_requests / 1000 * text_price.usd_per_1000
    details_cost = 0.0
    text_gross_cost = text_search_requests / 1000 * text_price.usd_per_1000
    return {
        "text_search_requests": text_search_requests,
        "details_requests": details_requests,
        "text_search_cost_usd": round(text_cost, 2),
        "details_cost_usd": round(details_cost, 2),
        "total_cost_usd": round(text_cost + details_cost, 2),
        "text_search_gross_cost_usd": round(text_gross_cost, 2),
        "total_gross_cost_usd": round(text_gross_cost + details_cost, 2),
        "free_cap_applied": include_monthly_free_cap,
        "pricing_note": "Schaetzung fuer Places API (New) Text Search Enterprise Global-Tarif; websiteUri/Telefonfelder liegen in Enterprise. Reale Rechnung haengt von SKUs, Kontingenten und Google Billing ab.",
    }


def format_cost_report(estimate: dict[str, float | int | str]) -> str:
    return "\n".join(
        [
            "Kosten-Schaetzung Google Places:",
            f"  Text Search (New) Requests: {estimate['text_search_requests']} -> ca. ${estimate['text_search_cost_usd']}",
            f"  Place Details (New) Requests: {estimate['details_requests']} -> ca. ${estimate['details_cost_usd']}",
            f"  Gesamt nach Free-Cap-Annahme: ca. ${estimate['total_cost_usd']}",
            f"  Gesamt ohne Free-Cap: ca. ${estimate['total_gross_cost_usd']}",
            f"  Hinweis: {estimate['pricing_note']}",
        ]
    )
