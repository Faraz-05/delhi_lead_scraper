"""
Resume from checkpoint: load saved raw leads, enrich, clean, and export.
Usage:
    python resume_export.py              # with website enrichment
    python resume_export.py --skip-enrich  # skip enrichment, just clean & export
"""

import argparse
import asyncio
import time

from scraper.enricher import enrich_leads
from pipeline.cleaner import clean_leads
from utils.exporter import export
from utils.checkpoint import load_checkpoint, save_checkpoint
from utils.logger import get_logger

log = get_logger("resume_export")


async def run(skip_enrich: bool = False) -> None:
    t0 = time.perf_counter()

    # Load raw leads from checkpoint
    raw = load_checkpoint("gmaps_raw")
    log.info("Loaded %d raw leads from checkpoint.", len(raw))
    if not raw:
        log.error("No checkpoint data found. Run main.py first.")
        return

    # Step 2: Enrichment
    if not skip_enrich:
        log.info("[2/4] Enriching leads via websites …")
        raw = await enrich_leads(raw)
        save_checkpoint("gmaps_enriched", raw)
    else:
        log.info("[2/4] Enrichment SKIPPED.")

    # Step 3: Cleaning
    log.info("[3/4] Running data-cleaning pipeline …")
    cleaned = clean_leads(raw)
    save_checkpoint("leads_cleaned", cleaned)
    log.info("[3/4] Clean leads: %d", len(cleaned))

    # Step 4: Export
    log.info("[4/4] Exporting to CSV & XLSX …")
    csv_path, xlsx_path = export(cleaned)
    log.info("[4/4] CSV  → %s", csv_path)
    log.info("[4/4] XLSX → %s", xlsx_path)

    elapsed = time.perf_counter() - t0
    log.info("Done in %.1f s — %d leads exported.", elapsed, len(cleaned))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--skip-enrich", action="store_true",
                   help="Skip website enrichment, just clean & export")
    args = p.parse_args()
    asyncio.run(run(skip_enrich=args.skip_enrich))
