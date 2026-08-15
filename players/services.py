import uuid

from .models import Player


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def find_player_by_identifier(identifier: str) -> Player | None:
    """Port of players.repository#findPlayerByIdentifier: id lookup, else a
    case-insensitive, trimmed name match (oldest row wins on ties)."""
    if is_uuid(identifier):
        return Player.objects.filter(pk=identifier).first()
    return (
        Player.objects.filter(name__iexact=identifier.strip())
        .order_by("created_at")
        .first()
    )


def resolve_canonical_player(identifier: str) -> Player | None:
    """Resolves an id/name to the canonical player, following merged_into_id
    once (merge chains are rejected at import time, so one hop is enough)."""
    row = find_player_by_identifier(identifier)
    if row is None:
        return None
    return row.merged_into or row


def get_family_ids(canonical_id) -> list[str]:
    """All raw player ids that roll up into this canonical id (itself + aliases)."""
    alias_ids = list(
        Player.objects.filter(merged_into_id=canonical_id).values_list("id", flat=True)
    )
    return [canonical_id, *alias_ids]


def get_player_identity_map() -> tuple[dict, dict]:
    """Maps every raw player id -> its canonical id, plus a display name per
    canonical id (trimmed, taken from the canonical row)."""
    canonical_id_by_raw_id: dict = {}
    name_by_canonical_id: dict = {}
    for row in Player.objects.values("id", "name", "merged_into_id"):
        canonical_id = row["merged_into_id"] or row["id"]
        canonical_id_by_raw_id[row["id"]] = canonical_id
        if not row["merged_into_id"]:
            name_by_canonical_id[row["id"]] = row["name"].strip()
    return canonical_id_by_raw_id, name_by_canonical_id
