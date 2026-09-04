import re
import unicodedata
from datetime import timedelta

import requests
from django.db import transaction
from django.utils import timezone

from .models import Commander, CommanderCardStat

EDHREC_JSON_URL = "https://json.edhrec.com/pages/commanders/{slug}.json"
EDHREC_COMMANDER_URL = "https://edhrec.com/commanders/{slug}"

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


def _slugify_single_name(name: str) -> str:
    """Transliterate accents to ASCII (e.g. "Éowyn" -> "eowyn" — a bare
    character-class strip would drop the E entirely), drop apostrophes
    rather than hyphenating them (EDHREC's own convention — "Saheeli, the
    Sun's Brilliance" -> "saheeli-the-suns-brilliance", not "...-sun-s-..."),
    lowercase, remaining punctuation hyphenated."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.replace("'", "")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower())
    return slug.strip("-")


def slugify_commander_name(name: str) -> str:
    """Best-effort EDHREC slug, verified against EDHREC's real URLs for both
    compound-name conventions used in this app's data:
    - Partner/background pairs ("A || B (Partners)") get each half's own
      slug concatenated — no "-partners" suffix.
    - Modal double-faced commanders ("A // B") use only the front face's
      slug; EDHREC doesn't slug the back face at all.
    Anything else this can't infer (e.g. a genuinely different naming
    scheme) should use Commander.edhrec_slug as a manual override."""
    if " || " in name:
        left, right = name.split(" || ", 1)
        right = re.sub(r"\s*\(partners\)\s*$", "", right, flags=re.IGNORECASE).strip()
        return f"{_slugify_single_name(left)}-{_slugify_single_name(right)}"
    if " // " in name:
        front_face = name.split(" // ", 1)[0]
        return _slugify_single_name(front_face)
    return _slugify_single_name(name)


def is_stale(commander: Commander) -> bool:
    return commander.edhrec_synced_at is None or (timezone.now() - commander.edhrec_synced_at) > STALE_AFTER


def get_edhrec_url(commander: Commander) -> str:
    slug = commander.edhrec_slug or slugify_commander_name(commander.name)
    return EDHREC_COMMANDER_URL.format(slug=slug)


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


def _extract_current_rank(payload: dict) -> int | None:
    """EDHREC has no single flat "rank" field — panels.rank_over_time is a
    dict keyed by month ("2026-07-01") tracking rank history for the
    site's trend chart; the latest month's `rank` is the commander's current
    overall EDHREC popularity rank."""
    rank_over_time = payload.get("panels", {}).get("rank_over_time")
    if not rank_over_time:
        return None
    latest_month = max(rank_over_time.keys())
    return rank_over_time[latest_month].get("rank")


def sync_commander_card_stats(commander_id) -> int:
    """Fetches this commander's EDHREC page and full-replaces its cached card
    stats. Returns the number of cards synced."""
    commander = Commander.objects.get(pk=commander_id)
    slug = commander.edhrec_slug or slugify_commander_name(commander.name)
    payload = _fetch_edhrec_payload(slug)
    rows = _flatten_card_stats(payload)
    rank = _extract_current_rank(payload)

    with transaction.atomic():
        CommanderCardStat.objects.filter(commander=commander).delete()
        if rows:
            CommanderCardStat.objects.bulk_create([CommanderCardStat(commander=commander, **row) for row in rows])
        commander.edhrec_synced_at = timezone.now()
        if rank is not None:
            commander.edhrec_rank = rank
        commander.save(update_fields=["edhrec_rank", "edhrec_synced_at", "updated_at"])

    return len(rows)


def get_commander_card_stats(commander_id):
    return CommanderCardStat.objects.filter(commander_id=commander_id).order_by("-inclusion_rate")


def _commanders_with_decks():
    return Commander.objects.filter(decks__isnull=False).distinct()


def get_edhrec_sync_status() -> dict:
    commanders = list(_commanders_with_decks())
    synced_ats = [c.edhrec_synced_at for c in commanders if c.edhrec_synced_at]
    return {
        "commander_count": len(commanders),
        "stale_count": sum(1 for c in commanders if is_stale(c)),
        "oldest_synced_at": min(synced_ats) if synced_ats else None,
        "newest_synced_at": max(synced_ats) if synced_ats else None,
        "failed_commander_names": [],
    }


def sync_all_commander_card_stats() -> dict:
    """Refreshes CommanderCardStat for every commander with an owned deck.
    One commander's EDHREC fetch failing (bad slug, timeout) shouldn't abort
    the rest of the batch — same resilience as sync_edhrec_stats.py's loop."""
    failed_names = []
    for commander in _commanders_with_decks():
        try:
            sync_commander_card_stats(commander.id)
        except requests.RequestException:
            failed_names.append(commander.name)

    status = get_edhrec_sync_status()
    status["failed_commander_names"] = failed_names
    return status
