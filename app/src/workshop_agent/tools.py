"""tools.py – Custom tools for querying structured Harry Potter data.

Team Slytherin's structured data integration for HORROCRUXES challenge.
Provides CSV query capabilities for characters and Horcruxes metadata.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Literal


# ── Paths to structured data sources ─────────────────────────────────────────

def _get_data_path() -> Path:
    """Return the absolute path to assets/data directory."""
    # Walk up from this file to find the repo root
    current = Path(__file__).parent
    while current.parent != current:
        assets_dir = current / "assets" / "data"
        if assets_dir.exists():
            return assets_dir
        # Also check one level up (when running from app/)
        assets_dir_alt = current.parent / "assets" / "data"
        if assets_dir_alt.exists():
            return assets_dir_alt
        current = current.parent
    raise FileNotFoundError("Could not locate assets/data directory")


DATA_DIR = _get_data_path()
HORCRUXES_CSV = DATA_DIR / "hp_horcruxes.csv"
CHARACTERS_CSV = DATA_DIR / "hp_characters.csv"


# ── CSV loader ────────────────────────────────────────────────────────────────

def _load_csv(file_path: Path) -> list[dict[str, str]]:
    """Load CSV file and return list of row dictionaries."""
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Query functions ───────────────────────────────────────────────────────────

def query_horcruxes(
    filter_by: str | None = None,
    value: str | None = None,
) -> str:
    """Query the Horcruxes structured database.

    Args:
        filter_by: Column name to filter by (e.g., 'destroyed_by', 'discovery_book')
        value: Value to match (case-insensitive substring match)

    Returns:
        Formatted string with matching Horcrux records.

    Examples:
        query_horcruxes() -> returns all 7 Horcruxes
        query_horcruxes("destroyed_by", "Harry") -> Horcruxes destroyed by Harry
        query_horcruxes("discovery_book", "Deathly Hallows") -> Horcruxes found in DH
    """
    rows = _load_csv(HORCRUXES_CSV)

    if filter_by and value:
        value_lower = value.lower()
        rows = [r for r in rows if value_lower in r.get(filter_by, "").lower()]

    if not rows:
        return f"No Horcruxes found matching filter: {filter_by}={value}"

    # Format output
    lines = [f"Found {len(rows)} Horcrux(es):\n"]
    for r in rows:
        lines.append(
            f"**Horcrux #{r['horcrux']}**: {r['object_type']}\n"
            f"  - Created: {r['creation_year']}\n"
            f"  - Discovered: {r['discovery_book']} ({r['discovery_chapter']})\n"
            f"  - Destroyed by: {r['destroyed_by']} using {r['destruction_method']}\n"
            f"  - Destruction: {r['destruction_book']} ({r['destruction_chapter']})\n"
            f"  - Location: {r['location_found']}\n"
        )

    return "\n".join(lines)


def query_characters(
    filter_by: str | None = None,
    value: str | None = None,
) -> str:
    """Query the Characters structured database.

    Args:
        filter_by: Column name to filter by (e.g., 'house', 'blood_status', 'allegiance')
        value: Value to match (case-insensitive substring match)

    Returns:
        Formatted string with matching character records.

    Examples:
        query_characters() -> returns all characters
        query_characters("house", "Slytherin") -> all Slytherin characters
        query_characters("allegiance", "Order") -> Order of the Phoenix members
        query_characters("blood_status", "Half-blood") -> all half-bloods
    """
    rows = _load_csv(CHARACTERS_CSV)

    if filter_by and value:
        value_lower = value.lower()
        rows = [r for r in rows if value_lower in r.get(filter_by, "").lower()]

    if not rows:
        return f"No characters found matching filter: {filter_by}={value}"

    # Format output
    lines = [f"Found {len(rows)} character(s):\n"]
    for r in rows:
        patronus = r.get('patronus', 'Unknown')
        death = r.get('death_book', 'Survived')
        lines.append(
            f"**{r['name']}** ({r['house']}, {r['blood_status']})\n"
            f"  - Role: {r['role']}\n"
            f"  - First appearance: {r['first_book']}\n"
            f"  - Patronus: {patronus}\n"
            f"  - Allegiance: {r.get('allegiance', 'Unknown')}\n"
            f"  - Status: {death}\n"
        )

    return "\n".join(lines)


def query_structured_data(
    data_type: Literal["horcruxes", "characters"],
    filter_by: str | None = None,
    value: str | None = None,
) -> str:
    """Unified interface for querying structured HP data.

    Args:
        data_type: Which dataset to query ('horcruxes' or 'characters')
        filter_by: Column name to filter by
        value: Value to match

    Returns:
        Formatted query results as a string.

    Examples:
        query_structured_data("horcruxes")
        query_structured_data("characters", "house", "Gryffindor")
        query_structured_data("horcruxes", "destroyed_by", "Hermione")
    """
    if data_type == "horcruxes":
        return query_horcruxes(filter_by, value)
    elif data_type == "characters":
        return query_characters(filter_by, value)
    else:
        return f"Unknown data_type: {data_type}. Use 'horcruxes' or 'characters'."
