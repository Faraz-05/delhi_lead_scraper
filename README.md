# Delhi Lead Generation Scraper

A scalable, async Python + Playwright pipeline that scrapes Google Maps for business leads in South & Central Delhi, enriches them via website crawling, and exports clean CSV/XLSX files.

## Features

- **Google Maps Automation** — Playwright-driven infinite-scroll scraping across configurable keyword × area combinations
- **Website Enrichment** — Visits company websites to extract emails (regex) and social links
- **Data Pipeline** — Cleans, validates, deduplicates, and filters leads to Delhi only
- **Checkpoint Recovery** — JSON-based checkpoints let you resume after interruptions
- **Production-Ready** — Logging, retries with backoff, rate-limiting, robots.txt awareness, proxy support

## Project Structure

```
delhi_lead_scraper/
├── main.py                 # Entry point & orchestration
├── config.py               # All configurable settings
├── requirements.txt        # Python dependencies
├── README.md
├── scraper/
│   ├── gmaps.py            # Google Maps Playwright scraper
│   └── enricher.py         # Website email & social-link extraction
├── pipeline/
│   └── cleaner.py          # Cleaning, validation, dedup, Delhi filter
├── utils/
│   ├── logger.py           # Rotating file + console logger
│   ├── checkpoint.py       # JSON checkpoint save/load
│   └── exporter.py         # CSV & XLSX export
├── output/                 # Generated leads.csv / leads.xlsx
├── checkpoints/            # Intermediate scraping state
└── logs/                   # Rotating log files
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Run full pipeline
python main.py
```

## CLI Options

```
python main.py                                        # Full pipeline
python main.py --skip-enrich                          # Skip website visits
python main.py --areas "Saket, Delhi"                 # Override areas
python main.py --keywords "Startups" "SaaS companies" # Override keywords
```

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---|---|---|
| `TARGET_AREAS` | 8 Delhi areas | Locations to search |
| `TARGET_KEYWORDS` | 7 industry types | Business types to search |
| `MAX_SCROLL_ATTEMPTS` | 60 | Scrolls per search query |
| `ENRICHMENT_CONCURRENCY` | 5 | Parallel browser tabs |
| `PROXY_SERVER` | `None` | HTTP proxy URL |
| `REQUEST_DELAY_MIN/MAX` | 1.5 – 4.0 s | Random delay range |
| `RESPECT_ROBOTS_TXT` | `True` | Obey robots.txt |

## Outputs

| File | Format | Description |
|---|---|---|
| `output/leads.csv` | CSV (UTF-8 BOM) | All cleaned leads |
| `output/leads.xlsx` | Excel | Same data in spreadsheet format |

## Legal & Safety

- Scrapes **publicly available** data only
- Respects `robots.txt` by default
- Implements random delays between requests
- Rate-limited concurrent connections
- No login / authentication bypass
