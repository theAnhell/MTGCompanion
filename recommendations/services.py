from django.conf import settings
from django.db import transaction
from django.utils import timezone

from binder.models import BinderCard
from cards.models import Card
from cards.services import get_deck_role_counts
from commanders.models import CommanderCardStat
from commanders.services import is_stale, sync_commander_card_stats
from decks.models import Deck, DeckCard

from .models import Recommendation

# No card-type field exists on DeckCard yet, so basics are excluded from
# removal candidates by name — a pragmatic v1 shortcut rather than a real
# type check.
BASIC_LAND_NAMES = {
    "Plains",
    "Island",
    "Swamp",
    "Mountain",
    "Forest",
    "Wastes",
    "Snow-Covered Plains",
    "Snow-Covered Island",
    "Snow-Covered Swamp",
    "Snow-Covered Mountain",
    "Snow-Covered Forest",
    "Snow-Covered Wastes",
}


def get_player_collection_card_names(player_id, exclude_deck_id=None) -> set[str]:
    """A player's collection = their binder + every card across their OTHER
    decks (per the product definition: binder + decks, excluding the deck
    being evaluated against itself)."""
    binder_names = set(BinderCard.objects.filter(player_id=player_id).values_list("card_name", flat=True))
    deck_cards = DeckCard.objects.filter(deck__owner_id=player_id)
    if exclude_deck_id:
        deck_cards = deck_cards.exclude(deck_id=exclude_deck_id)
    deck_names = set(deck_cards.values_list("card_name", flat=True))
    return binder_names | deck_names


def get_candidate_adds(deck_id, threshold: float | None = None) -> list[dict]:
    threshold = settings.RECOMMENDATION_ADD_THRESHOLD if threshold is None else threshold
    deck = Deck.objects.get(pk=deck_id)
    collection_names = get_player_collection_card_names(deck.owner_id, exclude_deck_id=deck.id)
    deck_card_names = set(deck.cards.values_list("card_name", flat=True))
    candidate_names = collection_names - deck_card_names
    if not candidate_names:
        return []
    stats = CommanderCardStat.objects.filter(
        commander_id=deck.commander_id, card_name__in=candidate_names, inclusion_rate__gte=threshold
    )
    return [{"card_name": s.card_name, "inclusion_rate": s.inclusion_rate} for s in stats]


def get_candidate_removes(deck_id, threshold: float | None = None, exclude_basics: bool = True) -> list[dict]:
    threshold = settings.RECOMMENDATION_REMOVE_THRESHOLD if threshold is None else threshold
    deck = Deck.objects.get(pk=deck_id)
    deck_cards = deck.cards.exclude(is_commander=True)
    if exclude_basics:
        deck_cards = deck_cards.exclude(card_name__in=BASIC_LAND_NAMES)
    deck_card_names = set(deck_cards.values_list("card_name", flat=True))
    if not deck_card_names:
        return []
    # Cards absent from EDHREC data entirely (no CommanderCardStat row) are
    # never flagged — we simply can't judge a card we have no data for.
    stats = CommanderCardStat.objects.filter(
        commander_id=deck.commander_id, card_name__in=deck_card_names, inclusion_rate__lte=threshold
    )
    return [{"card_name": s.card_name, "inclusion_rate": s.inclusion_rate} for s in stats]


def get_role_gap_adds(deck_id) -> list[dict]:
    """For each archetype role under target (settings.DECK_TARGET_*), suggest
    collection cards tagged with that role that also appear in the
    commander's own CommanderCardStat — the same trick that already keeps
    get_candidate_adds color-identity-safe for free, since a card absent from
    the commander's EDHREC list never gets suggested."""
    deck = Deck.objects.get(pk=deck_id)
    role_counts = get_deck_role_counts(deck_id)
    targets = {
        "ramp": settings.DECK_TARGET_RAMP,
        "draw": settings.DECK_TARGET_DRAW,
        "removal": settings.DECK_TARGET_REMOVAL,
        "land": settings.DECK_TARGET_LANDS,
    }

    collection_names = get_player_collection_card_names(deck.owner_id, exclude_deck_id=deck.id)
    deck_card_names = set(deck.cards.values_list("card_name", flat=True))
    candidate_names = collection_names - deck_card_names
    if not candidate_names:
        return []

    results = []
    for role, target in targets.items():
        gap = target - role_counts.get(role, 0)
        if gap <= 0:
            continue
        role_card_names = set(
            Card.objects.filter(name__in=candidate_names, roles__contains=[role]).values_list("name", flat=True)
        )
        if not role_card_names:
            continue
        stats = CommanderCardStat.objects.filter(
            commander_id=deck.commander_id, card_name__in=role_card_names
        ).order_by("-inclusion_rate")[:gap]
        results.extend({"card_name": s.card_name, "inclusion_rate": s.inclusion_rate, "role": role} for s in stats)
    return results


def list_recommendations(deck_id):
    return Recommendation.objects.filter(deck_id=deck_id).order_by("action", "-inclusion_rate")


def generate_recommendations(deck_id) -> list[Recommendation]:
    """Refreshes PROPOSED recommendations for a deck. APPROVED/IGNORED rows
    are left untouched — regeneration never overwrites a decision already
    made on a given (deck, action, card) triple."""
    deck = Deck.objects.select_related("commander").get(pk=deck_id)
    if is_stale(deck.commander):
        sync_commander_card_stats(deck.commander_id)

    # Role-gap adds take priority over plain inclusion-rate adds when a card
    # qualifies both ways — the role tag is the more specific, useful reason.
    adds_by_name: dict[str, dict] = {c["card_name"]: {**c, "role": None} for c in get_candidate_adds(deck_id)}
    for c in get_role_gap_adds(deck_id):
        adds_by_name[c["card_name"]] = c

    candidates = [(Recommendation.Action.ADD, c) for c in adds_by_name.values()] + [
        (Recommendation.Action.REMOVE, c) for c in get_candidate_removes(deck_id)
    ]

    with transaction.atomic():
        Recommendation.objects.filter(deck_id=deck_id, status=Recommendation.Status.PROPOSED).delete()

        decided_keys = set(
            Recommendation.objects.filter(deck_id=deck_id)
            .exclude(status=Recommendation.Status.PROPOSED)
            .values_list("action", "card_name")
        )
        rows = [
            Recommendation(
                player_id=deck.owner_id,
                deck_id=deck_id,
                action=action,
                card_name=candidate["card_name"],
                inclusion_rate=candidate["inclusion_rate"],
                role=candidate.get("role"),
            )
            for action, candidate in candidates
            if (action, candidate["card_name"]) not in decided_keys
        ]
        Recommendation.objects.bulk_create(rows)

    return list(list_recommendations(deck_id))


def update_recommendation(recommendation_id, status: str | None = None, applied: bool | None = None) -> Recommendation:
    rec = Recommendation.objects.get(pk=recommendation_id)
    update_fields = []
    if status is not None:
        rec.status = status
        update_fields.append("status")
    if applied is True:
        rec.applied_at = timezone.now()
        update_fields.append("applied_at")
    elif applied is False:
        rec.applied_at = None
        update_fields.append("applied_at")
    if update_fields:
        rec.save(update_fields=update_fields)
    return rec
