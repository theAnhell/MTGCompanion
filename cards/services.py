import gzip
import io
import json
import re

import requests
from django.db import transaction

from decks.models import DeckCard

from .models import Card

BULK_DATA_INDEX_URL = "https://api.scryfall.com/bulk-data"
# Scryfall rejects requests carrying a default HTTP-library User-Agent —
# it requires a custom one identifying the application.
SCRYFALL_REQUEST_HEADERS = {
    "User-Agent": "MythicTrack/1.0 (personal EDH stats tracker)",
    "Accept": "application/json",
}

LAND_TYPE_PATTERN = re.compile(r"\bLand\b")

# Deliberately a modest pattern set, not an exhaustive one — Scryfall's bulk
# data has no functional tags (those live only on the separate
# tagger.scryfall.com, with no bulk API), so roles are inferred from oracle
# text/type line. This will misclassify edge cases; tune the patterns against
# real decks over time rather than trying to get it perfect up front.
RAMP_PATTERNS = [
    re.compile(r"search your library for .*land card", re.IGNORECASE),
    re.compile(r"plays? an additional land", re.IGNORECASE),
    re.compile(r"put (a|that|the) land card.*onto the battlefield", re.IGNORECASE),
]
MANA_ABILITY_PATTERN = re.compile(r"\{T\}[^.]*:\s*add\b", re.IGNORECASE)

DRAW_PATTERNS = [
    re.compile(r"draws? (a|an|one|two|three|four|five|six|seven|\d+|that many|cards? equal to)", re.IGNORECASE),
]

REMOVAL_PATTERNS = [
    re.compile(r"destroy target", re.IGNORECASE),
    re.compile(r"exile target", re.IGNORECASE),
    re.compile(r"destroy all", re.IGNORECASE),
    re.compile(r"exile all", re.IGNORECASE),
    re.compile(r"target creature gets -\d+/-\d+", re.IGNORECASE),
    re.compile(r"deals? \d+ damage to (target|any target)", re.IGNORECASE),
    re.compile(r"fights? target creature", re.IGNORECASE),
]


def classify_roles(oracle_text: str | None, type_line: str | None) -> list[str]:
    oracle_text = oracle_text or ""
    type_line = type_line or ""
    roles = []

    if LAND_TYPE_PATTERN.search(type_line):
        roles.append("land")

    if any(p.search(oracle_text) for p in RAMP_PATTERNS):
        roles.append("ramp")
    elif "land" not in roles and MANA_ABILITY_PATTERN.search(oracle_text):
        roles.append("ramp")

    if any(p.search(oracle_text) for p in DRAW_PATTERNS):
        roles.append("draw")

    if any(p.search(oracle_text) for p in REMOVAL_PATTERNS):
        roles.append("removal")

    return roles


def _face_joined(card: dict, field: str) -> str:
    """Scryfall splits DFC/split-card data across `card_faces` when the
    top-level field is empty."""
    top_level = card.get(field)
    if top_level:
        return top_level
    faces = card.get("card_faces") or []
    return " // ".join(f.get(field, "") for f in faces if f.get(field))


def sync_scryfall_cards() -> int:
    """Fetches Scryfall's live bulk-data index, follows the Oracle Cards
    entry's current download URI, classifies every card, and full-replaces
    the Card table (same full-replace convention as
    commanders.sync_commander_card_stats and decks.replace_deck_cards).

    Scryfall serves Oracle Cards as gzip-compressed JSONL (one JSON object
    per line), not a plain JSON array — decompress and parse line by line
    rather than a single response.json() call."""
    index_response = requests.get(BULK_DATA_INDEX_URL, headers=SCRYFALL_REQUEST_HEADERS, timeout=30)
    index_response.raise_for_status()
    oracle_entry = next(entry for entry in index_response.json()["data"] if entry["type"] == "oracle_cards")

    response = requests.get(oracle_entry["jsonl_download_uri"], headers=SCRYFALL_REQUEST_HEADERS, timeout=180)
    response.raise_for_status()

    # Oracle Cards includes non-deck objects (tokens, emblems, art series,
    # etc.) that don't have unique names the way real cards do — e.g. many
    # unrelated "Soldier" tokens all share that exact name, which would
    # violate the name primary key. Skip those layouts entirely.
    non_card_layouts = {"token", "double_faced_token", "emblem", "art_series", "vanguard", "scheme", "planar", "augment"}

    rows_by_name: dict[str, Card] = {}
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            card = json.loads(line)
            name = card.get("name")
            if not name or card.get("layout") in non_card_layouts:
                continue
            oracle_text = _face_joined(card, "oracle_text")
            type_line = _face_joined(card, "type_line")
            # Defensive dedupe-by-name safety net (first occurrence wins) in
            # case any other edge case produces a duplicate name — a full
            # bulk_create fails entirely on one collision, so this keeps the
            # sync robust against cases the layout filter above doesn't catch.
            rows_by_name.setdefault(
                name,
                Card(
                    name=name,
                    scryfall_id=card.get("id"),
                    mana_cost=card.get("mana_cost"),
                    cmc=card.get("cmc"),
                    type_line=type_line,
                    oracle_text=oracle_text,
                    color_identity=card.get("color_identity"),
                    roles=classify_roles(oracle_text, type_line),
                ),
            )

    rows = list(rows_by_name.values())
    with transaction.atomic():
        Card.objects.all().delete()
        Card.objects.bulk_create(rows, batch_size=2000)

    return len(rows)


def get_sync_status() -> dict:
    latest = Card.objects.order_by("-synced_at").values_list("synced_at", flat=True).first()
    return {"card_count": Card.objects.count(), "synced_at": latest}


def get_deck_role_counts(deck_id) -> dict[str, int]:
    """Sums DeckCard.quantity per role by joining against Card.roles. Deck
    cards with no matching Card row (e.g. a name mismatch) are silently
    skipped — same "can't judge what we have no data for" stance as the
    recommendation engine."""
    counts = {"ramp": 0, "draw": 0, "removal": 0, "land": 0}
    deck_cards = DeckCard.objects.filter(deck_id=deck_id).exclude(is_commander=True)
    names = list(deck_cards.values_list("card_name", flat=True))
    roles_by_name = dict(Card.objects.filter(name__in=names).values_list("name", "roles"))

    for deck_card in deck_cards:
        for role in roles_by_name.get(deck_card.card_name, []):
            if role in counts:
                counts[role] += deck_card.quantity

    return counts
