"""
Central configuration for Delhi Lead Scraper.
All tunables live here — areas, industries, delays, paths, etc.
"""

import os

# ─── Project Paths ───────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ─── Target Areas ────────────────────────────────────────────────
TARGET_AREAS = [
    "Okhla Industrial Area, Delhi",
    "Nehru Place, Delhi",
    "Connaught Place, Delhi",
    "Saket, Delhi",
    "Jasola, Delhi",
    "Green Park, Delhi",
    "Lajpat Nagar, Delhi",
    "Bhikaji Cama Place, Delhi",
]

# ─── Target Industries / Keywords ───────────────────────────────
TARGET_KEYWORDS = [
    "Fintech companies",
    "Corporate headquarters",
    "Technology companies",
    "SaaS companies",
    "Consulting firms",
    "IT services companies",
    "Startups",
]

# ─── Google Maps ─────────────────────────────────────────────────
GMAPS_BASE_URL = "https://www.google.com/maps"
MAX_SCROLL_ATTEMPTS = 60          # per search query
SCROLL_PAUSE_SEC = 2.0            # pause between scrolls
PAGE_LOAD_TIMEOUT_MS = 60_000     # Playwright timeout

# ─── Website Enrichment ─────────────────────────────────────────
ENRICHMENT_TIMEOUT_SEC = 15       # per website
MAX_PAGES_PER_SITE = 5            # contact / about / home pages
ENRICHMENT_CONCURRENCY = 5        # parallel browser tabs

# ─── Rate Limiting & Safety ─────────────────────────────────────
REQUEST_DELAY_MIN = 1.5           # seconds
REQUEST_DELAY_MAX = 4.0           # seconds
RESPECT_ROBOTS_TXT = True
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ─── Retry ───────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 5

# ─── Proxy (set to None to disable) ─────────────────────────────
# Example: "http://user:pass@proxy.example.com:8080"
PROXY_SERVER = None

# ─── Delhi Pincode Ranges (for filtering) ───────────────────────
DELHI_PINCODE_PREFIXES = [
    "110",   # all Delhi pincodes start with 110
]

DELHI_KEYWORDS = [
    "delhi", "new delhi", "south delhi", "central delhi",
    "okhla", "nehru place", "connaught place", "saket",
    "jasola", "green park", "lajpat nagar", "bhikaji cama",
]

# ─── Output Filenames ───────────────────────────────────────────
CSV_FILENAME = "leads.csv"
XLSX_FILENAME = "leads.xlsx"
