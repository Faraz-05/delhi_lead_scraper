"""
JSON-based checkpoint system for crash / interrupt recovery.
Saves and loads intermediate scraping results so no work is lost.
"""

import json
import os
from typing import Any, Dict, List

from config import CHECKPOINT_DIR
from utils.logger import get_logger

log = get_logger("checkpoint")


def _checkpoint_path(name: str) -> str:
    return os.path.join(CHECKPOINT_DIR, f"{name}.json")


def save_checkpoint(name: str, data: List[Dict[str, Any]]) -> None:
    """Persist *data* under a named checkpoint."""
    path = _checkpoint_path(name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    log.info("Checkpoint saved: %s  (%d records)", path, len(data))


def load_checkpoint(name: str) -> List[Dict[str, Any]]:
    """Load a previous checkpoint. Returns [] if none exists."""
    path = _checkpoint_path(name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    log.info("Checkpoint loaded: %s  (%d records)", path, len(data))
    return data


def get_completed_queries(name: str = "completed_queries") -> set:
    """Return set of query strings already scraped (for resumption)."""
    data = load_checkpoint(name)
    return set(data)


def mark_query_complete(query: str, name: str = "completed_queries") -> None:
    """Append a query to the completed-queries checkpoint."""
    done = load_checkpoint(name)
    if query not in done:
        done.append(query)
        save_checkpoint(name, done)
