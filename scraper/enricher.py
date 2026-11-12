"""
Website enrichment module.

Given a list of raw leads (with a 'website' field), this module:
  1. Checks robots.txt for politeness.
  2. Visits the homepage, /contact, /about pages.
  3. Extracts emails (regex) and social-media links.
"""

import asyncio
import random
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

import config
from utils.logger import get_logger

log = get_logger("enricher")

# ── regex patterns ───────────────────────────────────────────────
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

SOCIAL_DOMAINS = {
    "linkedin.com": "linkedin",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "facebook.com": "facebook",
    "instagram.com": "instagram",
    "youtube.com": "youtube",
    "github.com": "github",
}

# paths to try on each website
SUBPAGES = ["/", "/contact", "/contact-us", "/about", "/about-us"]

# junk email patterns to skip
_JUNK_EMAIL_RE = re.compile(
    r"(example\.com|sentry\.io|wixpress|\.png|\.jpg|\.svg|\.gif|webpack|localhost)",
    re.I,
)


# ── robots.txt check ─────────────────────────────────────────────
def _is_allowed(url: str) -> bool:
    """Return True if robots.txt allows fetching *url* (or on any error)."""
    if not config.RESPECT_ROBOTS_TXT:
        return True
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True  # fail-open


async def _random_delay() -> None:
    await asyncio.sleep(
        random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
    )


# ── single site enrichment ──────────────────────────────────────
async def _enrich_one(page: Page, base_url: str) -> Dict[str, str]:
    """Visit *base_url* and its subpages; return extracted extras."""
    emails: set[str] = set()
    socials: dict[str, str] = {}

    for subpath in SUBPAGES[:config.MAX_PAGES_PER_SITE]:
        target = urljoin(base_url, subpath)
        if not _is_allowed(target):
            log.debug("Blocked by robots.txt: %s", target)
            continue
        try:
            await page.goto(
                target,
                timeout=config.ENRICHMENT_TIMEOUT_SEC * 1_000,
                wait_until="domcontentloaded",
            )
            await asyncio.sleep(1.5)
            body = await page.content()
        except Exception as exc:
            log.debug("Could not load %s: %s", target, exc)
            continue

        # Emails
        for m in EMAIL_RE.finditer(body):
            email = m.group(0).lower()
            if not _JUNK_EMAIL_RE.search(email):
                emails.add(email)

        # Social links
        try:
            anchors = await page.locator("a[href]").all()
            for a in anchors:
                href = await a.get_attribute("href")
                if not href:
                    continue
                for social_domain, label in SOCIAL_DOMAINS.items():
                    if social_domain in href and label not in socials:
                        socials[label] = href.strip()
        except Exception:
            pass

        await _random_delay()

    return {
        "email": "; ".join(sorted(emails)) if emails else "",
        "social_links": "; ".join(f"{k}: {v}" for k, v in socials.items()) if socials else "",
    }


# ── batch enrichment ─────────────────────────────────────────────
async def enrich_leads(leads: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    For each lead with a *website*, open it and pull emails + socials.
    Processes leads sequentially to avoid cascading browser crashes.
    Saves progress every 25 leads.
    """
    if not leads:
        return leads

    # Only enrich leads that have a website and haven't been enriched yet
    to_enrich = [
        (i, l) for i, l in enumerate(leads)
        if l.get("website") and not l.get("_enriched")
    ]
    log.info(
        "Starting website enrichment: %d leads with websites (out of %d total).",
        len(to_enrich), len(leads),
    )

    if not to_enrich:
        log.info("All leads already enriched or have no website. Skipping.")
        return leads

    proxy_cfg = {"server": config.PROXY_SERVER} if config.PROXY_SERVER else None

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=True)
        context: BrowserContext = await browser.new_context(
            user_agent=config.USER_AGENT,
            proxy=proxy_cfg,
        )

        for count, (idx, lead) in enumerate(to_enrich, start=1):
            url = lead.get("website", "")
            if not url.startswith("http"):
                url = f"https://{url}"

            page = None
            try:
                page = await context.new_page()
                extras = await _enrich_one(page, url)
                lead.update(extras)
                lead["_enriched"] = "1"
                status = f"email={'YES' if extras.get('email') else 'no'}"
                log.info(
                    "  [%d/%d] ✓ %s  (%s)",
                    count, len(to_enrich),
                    lead.get("company_name", "?"), status,
                )
            except Exception as exc:
                lead["_enriched"] = "1"  # mark so we don't retry forever
                log.warning(
                    "  [%d/%d] ✗ %s — %s",
                    count, len(to_enrich),
                    lead.get("company_name", "?"), exc,
                )
            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass

            # Save checkpoint every 25 leads
            if count % 25 == 0:
                from utils.checkpoint import save_checkpoint
                save_checkpoint("gmaps_enriched", leads)
                log.info("  … checkpoint saved (%d/%d done)", count, len(to_enrich))

        await browser.close()

    # Remove internal marker before returning
    for l in leads:
        l.pop("_enriched", None)

    enriched_count = sum(1 for l in leads if l.get("email"))
    log.info("Enrichment done. %d / %d leads have emails.", enriched_count, len(leads))
    return leads

