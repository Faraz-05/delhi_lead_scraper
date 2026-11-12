"""
Data cleaning, validation, deduplication, and Delhi-area filtering.
"""

import re
from typing import Dict, List

import config
from utils.logger import get_logger

log = get_logger("cleaner")


# ── helpers ──────────────────────────────────────────────────────
_EMAIL_VALID_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def _is_valid_email(email: str) -> bool:
    return bool(_EMAIL_VALID_RE.match(email.strip()))


def _normalise_phone(phone: str) -> str:
    """Keep last 10 digits only."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("91") and len(digits) > 10:
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits


def _is_delhi(lead: Dict[str, str]) -> bool:
    """Check whether the lead's address or pincode indicates Delhi."""
    address = lead.get("address", "").lower()
    pincode = lead.get("pincode", "")

    # Pincode check
    if pincode:
        for prefix in config.DELHI_PINCODE_PREFIXES:
            if pincode.startswith(prefix):
                return True

    # Keyword check
    for kw in config.DELHI_KEYWORDS:
        if kw in address:
            return True

    return False


# ── main pipeline ────────────────────────────────────────────────
def clean_leads(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Run full cleaning → validation → dedup → Delhi filter pipeline."""
    log.info("Cleaning pipeline started with %d raw records.", len(raw))
    cleaned: List[Dict[str, str]] = []

    for lead in raw:
        # ── Basic cleaning ──
        lead = {k: (v.strip() if isinstance(v, str) else v) for k, v in lead.items()}

        # Drop records without a company name
        if not lead.get("company_name"):
            continue

        # ── Phone normalisation ──
        lead["phone"] = _normalise_phone(lead.get("phone", ""))

        # ── Email validation ──
        emails_raw = lead.get("email", "")
        valid_emails = [
            e.strip()
            for e in emails_raw.split(";")
            if _is_valid_email(e)
        ]
        lead["email"] = "; ".join(valid_emails)

        # ── Pincode extraction (fallback) ──
        if not lead.get("pincode"):
            match = re.search(r"\b(1[0-9]{5})\b", lead.get("address", ""))
            lead["pincode"] = match.group(1) if match else ""

        cleaned.append(lead)

    log.info("After basic cleaning: %d records.", len(cleaned))

    # ── Delhi filtering ──
    delhi_only = [l for l in cleaned if _is_delhi(l)]
    log.info("After Delhi filter: %d records.", len(delhi_only))

    # ── Deduplication by (phone, domain) ──
    seen_phones: set[str] = set()
    seen_domains: set[str] = set()
    deduped: List[Dict[str, str]] = []

    for lead in delhi_only:
        phone = lead.get("phone", "")
        domain = lead.get("domain", "").lower()

        if phone and phone in seen_phones:
            continue
        if domain and domain in seen_domains:
            continue

        if phone:
            seen_phones.add(phone)
        if domain:
            seen_domains.add(domain)
        deduped.append(lead)

    log.info("After deduplication: %d records.", len(deduped))
    return deduped
