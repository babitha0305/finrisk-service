"""Rules-based risk-theme tagger (transparent, auditable keyword taxonomy)."""
import re

THEMES: dict[str, list[str]] = {
    "supply_chain": ["supplier", "supply", "shipment", "port", "ports", "foundry",
                     "manufacturer", "manufacturers", "shortage", "tariff", "tariffs",
                     "shipping", "raw materials", "carriers"],
    "cyber": ["breach", "security incident", "ransomware", "cyber", "payment card data"],
    "regulatory": ["regulation", "regulatory", "approval", "compliance", "legislation",
                   "fda", "data protection rules", "capital and liquidity"],
    "interest_rate": ["interest rate", "interest rates", "net interest margin", "bond"],
    "credit": ["loan", "defaults", "credit losses", "solvency"],
    "commodity": ["oil", "natural gas", "fuel", "carbon pricing"],
    "fx": ["exchange rate", "currencies", "currency"],
    "litigation": ["litigation", "patent", "damages", "fines"],
    "demand": ["demand", "consumer", "spending", "churn", "cyclical"],
    "operational": ["outage", "accidents", "pipeline", "blowouts", "catastrophic"],
}

_PATTERNS = {
    theme: [re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE) for k in kws]
    for theme, kws in THEMES.items()
}


def tag_text(text: str) -> list[str]:
    """Return the sorted list of themes whose keywords appear in `text`."""
    return sorted(t for t, pats in _PATTERNS.items() if any(p.search(text) for p in pats))
