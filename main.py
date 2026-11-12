"""
Delhi Lead Scraper — main orchestration entry-point.

Usage:
    python main.py                 # full pipeline
    python main.py --skip-enrich   # maps only, skip website visits
    python main.py --areas "Saket, Delhi" "Nehru Place, Delhi"
    python main.py --keywords "Startups" "Fintech companies"
"""

import argparse
import asyncio
import sys
import time

import config
from scraper.gmaps import scrape_google_maps
from scraper.enricher import enrich_leads
from pipeline.cleaner import clean_leads
from utils.exporter import export
from utils.checkpoint import save_checkpoint
from utils.logger import get_logger

log = get_logger("main")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Delhi Lead Generation Scraper")
    p.add_argument(
        "--keywords",
        nargs="*",
        default=None,
        help="Override target keywords (default: config.TARGET_KEYWORDS)",
    )
    p.add_argument(
        "--areas",
        nargs="*",
        default=None,
        help="Override target areas (default: config.TARGET_AREAS)",
    )
    p.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Skip the website enrichment step",
    )
    p.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    return p.parse_args()


async def run(args: argparse.Namespace) -> None:
    t0 = time.perf_counter()
    log.info("=" * 60)
    log.info("  Delhi Lead Generation Scraper — starting")
    log.info("=" * 60)

    # ── Step 1: Google Maps scraping ─────────────────────────────
    log.info("[1/4] Scraping Google Maps …")
    raw_leads = await scrape_google_maps(
        keywords=args.keywords,
        areas=args.areas,
    )
    log.info("[1/4] Raw leads collected: %d", len(raw_leads))

    # ── Step 2: Website enrichment ───────────────────────────────
    if not args.skip_enrich:
        log.info("[2/4] Enriching leads via websites …")
        raw_leads = await enrich_leads(raw_leads)
    else:
        log.info("[2/4] Website enrichment SKIPPED.")

    # ── Step 3: Cleaning pipeline ────────────────────────────────
    log.info("[3/4] Running data-cleaning pipeline …")
    clean = clean_leads(raw_leads)
    save_checkpoint("leads_cleaned", clean)
    log.info("[3/4] Clean leads: %d", len(clean))

    # ── Step 4: Export ───────────────────────────────────────────
    log.info("[4/4] Exporting to CSV & XLSX …")
    csv_path, xlsx_path = export(clean)
    log.info("[4/4] Files saved:")
    log.info("       CSV  → %s", csv_path)
    log.info("       XLSX → %s", xlsx_path)

    elapsed = time.perf_counter() - t0
    log.info("=" * 60)
    log.info("  Done in %.1f s  — %d leads exported.", elapsed, len(clean))
    log.info("=" * 60)


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        log.warning("Interrupted. Progress saved via checkpoints.")
        sys.exit(1)


if __name__ == "__main__":
    main()
