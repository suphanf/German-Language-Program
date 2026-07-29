"""Parser for the Markdown-formatted German vocabulary list.

Turns ``data/german_a1_vocabulary.md`` into a list of :class:`Group` objects,
each holding the :class:`Word` entries to practice.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

GROUP_HEADER_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^-\s+(.*\S)\s*$")
PAREN_RE = re.compile(r"\([^()]*\)")
BOLD_RE = re.compile(r"\*\*")
ITALIC_RE = re.compile(r"\*")
SEPARATOR_CHAR = "–"  # en dash "–"


@dataclass
class Word:
    german_display: str   # full German text (bold markers stripped) shown after answering
    english: str           # English meaning shown as the prompt
    accepted: list[str]    # normalized acceptable German answers


@dataclass
class Group:
    number: int
    title: str
    words: list[Word] = field(default_factory=list)


def _find_separator(text: str) -> int | None:
    """Return the index of the first en dash at paren-depth 0, or None."""
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == SEPARATOR_CHAR and depth == 0:
            return i
    return None


def _clean_answer(text: str) -> str:
    text = PAREN_RE.sub("", text)
    text = BOLD_RE.sub("", text)
    text = text.replace("|", "")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.rstrip(".").strip()
    return text


def normalize_user_answer(text: str) -> str:
    """Apply the same leniency rules to the user's typed answer."""
    text = PAREN_RE.sub("", text)
    text = text.replace("|", "")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.rstrip(".").strip()
    return text


def _parse_bullet(raw: str) -> Word | None:
    idx = _find_separator(raw)
    if idx is None:
        return None
    german_part = raw[:idx].strip()
    english_part = raw[idx + 1 :].strip()
    if not german_part or not english_part:
        return None

    german_display = re.sub(r"\s+", " ", BOLD_RE.sub("", german_part)).strip()
    english_display = re.sub(r"\s+", " ", ITALIC_RE.sub("", english_part)).strip()

    accepted: list[str] = []
    for alt in PAREN_RE.sub("", german_part).split("/"):
        cleaned = _clean_answer(alt)
        if cleaned and cleaned not in accepted:
            accepted.append(cleaned)

    if not accepted:
        return None

    return Word(german_display=german_display, english=english_display, accepted=accepted)


def parse_vocabulary(path: str) -> list[Group]:
    groups: list[Group] = []
    current: Group | None = None

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            header_match = GROUP_HEADER_RE.match(line)
            if header_match:
                current = Group(number=int(header_match.group(1)), title=header_match.group(2))
                groups.append(current)
                continue

            bullet_match = BULLET_RE.match(line)
            if bullet_match and current is not None:
                word = _parse_bullet(bullet_match.group(1))
                if word is not None:
                    current.words.append(word)

    return groups
