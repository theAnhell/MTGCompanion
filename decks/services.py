from .models import Deck, DeckCard, RetiredDeck


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


def list_deck_cards(deck_id):
    return DeckCard.objects.filter(deck_id=deck_id).order_by("card_name")


def replace_deck_cards(deck_id, rows: list[dict]) -> None:
    """Fully replaces a deck's stored decklist (a Moxfield export is a
    snapshot, not a diff), mirroring deck-cards.repository#replaceDeckCards."""
    DeckCard.objects.filter(deck_id=deck_id).delete()
    if not rows:
        return
    DeckCard.objects.bulk_create([DeckCard(deck_id=deck_id, **row) for row in rows])


def list_player_decks(player_id):
    return (
        Deck.objects.filter(owner_id=player_id)
        .select_related("commander", "owner")
        .prefetch_related("cards")
        .order_by("commander__name")
    )


def get_deck(deck_id):
    return (
        Deck.objects.select_related("commander", "owner").prefetch_related("cards").filter(pk=deck_id).first()
    )
