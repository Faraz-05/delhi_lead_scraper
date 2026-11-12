"""
Google Maps Playwright scraper.

Searches for each (keyword, area) combination, scrolls the results panel
to load all listings, then extracts business card data.
"""

import asyncio
import random
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PwTimeout,
)

import config
from utils.logger import get_logger
from utils.checkpoint import (
    get_completed_queries,
    mark_query_complete,
    save_checkpoint,
    load_checkpoint,
)

log = get_logger("gmaps_scraper")


# ── helpers ──────────────────────────────────────────────────────
def _clean_phone(raw: Optional[str]) -> str:
    """Strip non-digit chars and remove leading +91 / 91."""
    if not raw:
        return ""
    digits = re.sub(r"[^\d]", "", raw)
    if digits.startswith("91") and len(digits) > 10:
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits


def _extract_domain(url: Optional[str]) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.lower().replace("www.", "")
        return domain
    except Exception:
        return ""


async def _random_delay() -> None:
    await asyncio.sleep(
        random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
    )


# ── scrolling ────────────────────────────────────────────────────
async def _scroll_results(page: Page) -> None:
    """Scroll the left-hand results pane until no more items load."""
    scrollable = page.locator('div[role="feed"]')
    try:
        await scrollable.wait_for(state="attached", timeout=10_000)
    except PwTimeout:
        log.warning("Results feed not found — page might have no results.")
        return

    prev_count = 0
    stale_rounds = 0
    for _ in range(config.MAX_SCROLL_ATTEMPTS):
        await scrollable.evaluate("el => el.scrollTop = el.scrollHeight")
        await asyncio.sleep(config.SCROLL_PAUSE_SEC)

        items = await page.locator('div[role="feed"] > div > div > a').count()
        if items == prev_count:
            stale_rounds += 1
            if stale_rounds >= 3:
                log.debug("Scroll settled after %d items.", items)
                break
        else:
            stale_rounds = 0
            prev_count = items

        # Check for "end of list" marker
        end_marker = page.locator("span.HlvSq")
        if await end_marker.count() > 0:
            log.debug("End-of-list marker detected.")
            break

    log.info("Total listing links visible after scrolling: %d", prev_count)


# ── single listing extraction ────────────────────────────────────
async def _extract_listing(page: Page) -> Dict[str, str]:
    """Extract data from a single open listing panel."""
    data: Dict[str, str] = {}

    # Company name
    try:
        name_el = page.locator("h1.DUwDvf")
        data["company_name"] = (await name_el.inner_text(timeout=3_000)).strip()
    except Exception:
        data["company_name"] = ""

    # Category
    try:
        cat_el = page.locator('button[jsaction="pane.rating.category"]')
        data["category"] = (await cat_el.inner_text(timeout=2_000)).strip()
    except Exception:
        data["category"] = ""

    # Address
    try:
        addr_el = page.locator(
            'button[data-item-id="address"] div.Io6YTe, '
            'div[data-item-id="address"] div.Io6YTe'
        )
        data["address"] = (await addr_el.first.inner_text(timeout=2_000)).strip()
    except Exception:
        data["address"] = ""

    # Pincode
    pincode_match = re.search(r"\b(1[0-9]{5})\b", data.get("address", ""))
    data["pincode"] = pincode_match.group(1) if pincode_match else ""

    # Phone
    try:
        phone_el = page.locator(
            'button[data-item-id^="phone"] div.Io6YTe, '
            'div[data-item-id^="phone"] div.Io6YTe'
        )
        raw_phone = (await phone_el.first.inner_text(timeout=2_000)).strip()
        data["phone"] = _clean_phone(raw_phone)
    except Exception:
        data["phone"] = ""

    # Website
    try:
        web_el = page.locator(
            'a[data-item-id="authority"], '
            'a[data-item-id^="authority"]'
        )
        href = await web_el.first.get_attribute("href", timeout=2_000)
        data["website"] = href or ""
        data["domain"] = _extract_domain(href)
    except Exception:
        data["website"] = ""
        data["domain"] = ""

    return data


# ── main scrape loop ─────────────────────────────────────────────
async def scrape_google_maps(
    keywords: List[str] | None = None,
    areas: List[str] | None = None,
) -> List[Dict[str, str]]:
    """
    Launch Playwright, iterate keywords × areas, scroll + extract.
    Resumes from checkpoint automatically.
    """
    keywords = keywords or config.TARGET_KEYWORDS
    areas = areas or config.TARGET_AREAS
    completed = get_completed_queries()
    all_leads: List[Dict[str, str]] = load_checkpoint("gmaps_raw")

    log.info(
        "Starting Google Maps scraper  — %d keywords × %d areas  (%d already done)",
        len(keywords), len(areas), len(completed),
    )

    proxy_cfg = {"server": config.PROXY_SERVER} if config.PROXY_SERVER else None

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context: BrowserContext = await browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            proxy=proxy_cfg,
        )
        page: Page = await context.new_page()

        for kw in keywords:
            for area in areas:
                query = f"{kw} in {area}"
                if query in completed:
                    log.info("SKIP (already done): %s", query)
                    continue

                log.info("── Searching: %s", query)
                search_url = (
                    f"{config.GMAPS_BASE_URL}/search/{query.replace(' ', '+')}"
                )

                for attempt in range(1, config.MAX_RETRIES + 1):
                    try:
                        await page.goto(
                            search_url,
                            timeout=config.PAGE_LOAD_TIMEOUT_MS,
                            wait_until="domcontentloaded",
                        )
                        await asyncio.sleep(3)  # let JS render
                        await _scroll_results(page)
                        break
                    except Exception as exc:
                        log.warning(
                            "Attempt %d failed for '%s': %s", attempt, query, exc
                        )
                        if attempt == config.MAX_RETRIES:
                            log.error("Giving up on '%s' after %d attempts.", query, config.MAX_RETRIES)
                            continue
                        await asyncio.sleep(config.RETRY_BACKOFF_SEC * attempt)

                # ── Pass 1: collect all listing hrefs ──
                links = page.locator('div[role="feed"] > div > div > a')
                link_count = await links.count()
                log.info("Found %d listing links for '%s'", link_count, query)

                listing_urls: list[str] = []
                for idx in range(link_count):
                    try:
                        href = await links.nth(idx).get_attribute("href", timeout=2_000)
                        if href and "/maps/place/" in href:
                            listing_urls.append(href)
                    except Exception:
                        pass
                log.info("Collected %d valid listing URLs.", len(listing_urls))

                # ── Pass 2: visit each listing URL directly ──
                for idx, url in enumerate(listing_urls):
                    try:
                        await page.goto(url, timeout=config.PAGE_LOAD_TIMEOUT_MS,
                                        wait_until="domcontentloaded")
                        await asyncio.sleep(2)
                        lead = await _extract_listing(page)
                        lead["search_query"] = query
                        if lead.get("company_name"):
                            all_leads.append(lead)
                            log.info("  [%d/%d] ✓ %s", idx + 1, len(listing_urls),
                                     lead["company_name"])
                        await _random_delay()
                    except Exception as exc:
                        log.warning("  [%d/%d] Listing skipped: %s",
                                    idx + 1, len(listing_urls), exc)

                mark_query_complete(query)
                save_checkpoint("gmaps_raw", all_leads)
                await _random_delay()

        await browser.close()

    log.info("Google Maps scraping complete. Total raw leads: %d", len(all_leads))
    return all_leads
