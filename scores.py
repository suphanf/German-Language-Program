"""Persistence for the latest practice score of each vocabulary group."""
from __future__ import annotations

import json
import os
from datetime import datetime

SCORES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scores.json")


def load_scores() -> dict[int, dict]:
    if not os.path.exists(SCORES_PATH):
        return {}
    try:
        with open(SCORES_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return {int(k): v for k, v in raw.items()}


def save_score(group_number: int, correct: int, total: int) -> None:
    scores = load_scores()
    scores[group_number] = {
        "correct": correct,
        "total": total,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(os.path.dirname(SCORES_PATH), exist_ok=True)
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in scores.items()}, f, indent=2)


def format_elapsed(timestamp: str) -> str:
    """Human-readable time since ``timestamp`` (an isoformat local time)."""
    then = datetime.fromisoformat(timestamp)
    seconds = max(0, (datetime.now() - then).total_seconds())

    if seconds < 86400:
        hours = int(seconds // 3600)
        if hours < 1:
            return "less than 1 hour ago"
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    days = int(seconds // 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"
