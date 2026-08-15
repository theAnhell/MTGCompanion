from .models import DeckCard, RetiredDeck


def list_retired_decks_for_family(player_family_ids: list):
    if not player_family_ids:
        return RetiredDeck.objects.none()
    return RetiredDeck.objects.filter(player_id__in=player_family_ids)


def get_retired_commander_id_set(player_family_ids: list) -> set:
    return set(
        list_retired_decks_for_family(player_family_ids).values_list("commander_id", flat=True)
    )


def add_retired_deck(player_id, commander_id, source: str = "manual") -> None:
    RetiredDeck.objects.get_or_create(
        player_id=player_id, commander_id=commander_id, defaults={"source": source}
    )


def remove_retired_deck(player_id, commander_id) -> None:
    RetiredDeck.objects.filter(player_id=player_id, commander_id=commander_id).delete()


def list_retired_decks_with_commander_info(player_family_ids: list):
    if not player_family_ids:
        return RetiredDeck.objects.none()
    return (
        RetiredDeck.objects.filter(player_id__in=player_family_ids)
        .select_related("commander")
        .order_by("commander__name")
    )


def bulk_insert_retired_decks(rows: list[dict]) -> None:
    if not rows:
        return
    RetiredDeck.objects.bulk_create(
        [RetiredDeck(**row) for row in rows], ignore_conflicts=True
    )


def list_deck_cards(commander_id):
    return DeckCard.objects.filter(commander_id=commander_id).order_by("card_name")


def replace_deck_cards(commander_id, rows: list[dict]) -> None:
    """Fully replaces a commander's stored decklist (a Moxfield export is a
    snapshot, not a diff), mirroring deck-cards.repository#replaceDeckCards."""
    DeckCard.objects.filter(commander_id=commander_id).delete()
    if not rows:
        return
    DeckCard.objects.bulk_create([DeckCard(commander_id=commander_id, **row) for row in rows])
