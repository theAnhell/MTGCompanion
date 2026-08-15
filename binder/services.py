from .models import BinderCard


def list_binder_cards(player_id):
    return BinderCard.objects.filter(player_id=player_id).order_by("card_name")


def replace_binder_cards(player_id, rows: list[dict]) -> None:
    """Fully replaces a player's stored binder (a Moxfield export is a
    snapshot, not a diff), mirroring decks.services#replace_deck_cards."""
    BinderCard.objects.filter(player_id=player_id).delete()
    if not rows:
        return
    BinderCard.objects.bulk_create([BinderCard(player_id=player_id, **row) for row in rows])
