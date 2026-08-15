import re
from datetime import timedelta

import requests
from django.db import transaction
from django.utils import timezone

from .models import Commander, CommanderCardStat

EDHREC_JSON_URL = "https://json.edhrec.com/pages/commanders/{slug}.json"

# The exhaustive, non-overlapping card-type breakdown of a commander's page.
# "New Cards" / "Top Cards" / "High Synergy Cards" / "Game Changers" are
# cross-cutting subsets of these same cards and are deliberately excluded —
# folding them in would double-count entries already covered here.
EDHREC_TYPE_CATEGORY_TAGS = {
    "creatures",
    "instants",
    "sorceries",
    "utilityartifacts",
    "enchantments",
    "battles",
    "planeswalkers",
    "utilitylands",
    "manaartifacts",
    "lands",
}

STALE_AFTER = timedelta(days=14)


def slugify_commander_name(name: str) -> str:
    """Best-effort EDHREC slug: lowercase, punctuation stripped, spaces
    hyphenated. Doesn't handle partner/background combined-slug URLs — use
    Commander.edhrec_slug to override those."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return slug.strip("-")


def is_stale(commander: Commander) -> bool:
    return commander.edhrec_synced_at is None or (timezone.now() - commander.edhrec_synced_at) > STALE_AFTER


def _fetch_edhrec_payload(slug: str) -> dict:
    response = requests.get(EDHREC_JSON_URL.format(slug=slug), timeout=10)
    response.raise_for_status()
    return response.json()


def _flatten_card_stats(payload: dict) -> list[dict]:
    cardlists = payload.get("container", {}).get("json_dict", {}).get("cardlists", [])
    by_name: dict[str, dict] = {}
    for cardlist in cardlists:
        if cardlist.get("tag") not in EDHREC_TYPE_CATEGORY_TAGS:
            continue
        category = cardlist.get("header", cardlist.get("tag"))
        for card in cardlist.get("cardviews", []):
            name = card.get("name")
            num_decks = card.get("num_decks")
            potential_decks = card.get("potential_decks")
            if not name or not potential_decks:
                continue
            by_name[name] = {
                "card_name": name,
                "category": category,
                "num_decks": num_decks,
                "potential_decks": potential_decks,
                "synergy": card.get("synergy"),
                "inclusion_rate": round((num_decks / potential_decks) * 100, 1),
            }
    return list(by_name.values())


def sync_commander_card_stats(commander_id) -> int:
    """Fetches this commander's EDHREC page and full-replaces its cached card
    stats. Returns the number of cards synced."""
    commander = Commander.objects.get(pk=commander_id)
    slug = commander.edhrec_slug or slugify_commander_name(commander.name)
    payload = _fetch_edhrec_payload(slug)
    rows = _flatten_card_stats(payload)

    with transaction.atomic():
        CommanderCardStat.objects.filter(commander=commander).delete()
        if rows:
            CommanderCardStat.objects.bulk_create([CommanderCardStat(commander=commander, **row) for row in rows])
        commander.edhrec_synced_at = timezone.now()
        commander.save(update_fields=["edhrec_synced_at", "updated_at"])

    return len(rows)


def get_commander_card_stats(commander_id):
    return CommanderCardStat.objects.filter(commander_id=commander_id).order_by("-inclusion_rate")
