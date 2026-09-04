from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from cards.services import get_deck_role_counts
from commanders.models import Commander
from commanders.services import get_commander_card_stats
from imports.moxfield_parser import extract_moxfield_deck_id, is_commander_card, parse_moxfield_export
from players.services import get_family_ids, resolve_canonical_player

from .models import Deck
from .serializers import DeckDetailSerializer, DeckSerializer, RetiredDeckSerializer
from .services import (
    add_retired_deck,
    get_deck,
    list_player_decks,
    list_retired_decks_with_commander_info,
    remove_retired_deck,
    replace_deck_cards,
)


def _deck_detail_context(commander_id) -> dict:
    stats_by_card_name = {s.card_name: s.inclusion_rate for s in get_commander_card_stats(commander_id)}
    return {"stats_by_card_name": stats_by_card_name}


def _require_canonical_player(identifier):
    player = resolve_canonical_player(identifier)
    if player is None:
        raise NotFound(f"Player not found: {identifier}")
    return player


def _parse_export_to_rows(export_text: str, commander_name: str) -> list[dict]:
    parsed = parse_moxfield_export(export_text)
    if not parsed:
        raise ValidationError("No cards could be parsed from exportText")
    return [
        {
            "card_name": card["cardName"],
            "set_code": card["setCode"],
            "collector_number": card["collectorNumber"],
            "quantity": card["quantity"],
            "is_foil": card["isFoil"],
            "is_commander": is_commander_card(card["cardName"], commander_name),
        }
        for card in parsed
    ]


class RetiredDecksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        family_ids = get_family_ids(player.id)
        rows = list_retired_decks_with_commander_info(family_ids)
        return Response(RetiredDeckSerializer(rows, many=True).data)

    def post(self, request, id):
        player = _require_canonical_player(id)
        commander_id = request.data.get("commanderId")
        if not isinstance(commander_id, str):
            raise ValidationError("Body must include commanderId")
        commander = Commander.objects.filter(pk=commander_id).first()
        if commander is None:
            raise NotFound(f"Commander not found: {commander_id}")
        add_retired_deck(player.id, commander_id, "manual")
        return Response(
            {"playerId": str(player.id), "commanderId": commander_id, "source": "manual"},
            status=HTTP_201_CREATED,
        )


class RetiredDeckDetailView(APIView):
    def delete(self, request, id, commander_id):
        player = _require_canonical_player(id)
        remove_retired_deck(player.id, commander_id)
        return Response(status=HTTP_204_NO_CONTENT)


class DeckListCreateView(APIView):
    """Owned decks (a player's own builds), not to be confused with
    /players/<id>/decks under the stats app, which reports game-history
    stats per commander a player has piloted."""

    def get(self, request):
        player_id = request.query_params.get("playerId")
        if not player_id:
            raise ValidationError("playerId query parameter is required")
        player = _require_canonical_player(player_id)
        decks = list_player_decks(player.id)
        return Response(DeckSerializer(decks, many=True).data)

    def post(self, request):
        owner_id = request.data.get("ownerId")
        commander_id = request.data.get("commanderId")
        export_text = request.data.get("exportText")
        if not owner_id or not commander_id or not export_text:
            raise ValidationError("Body must include ownerId, commanderId, and exportText")

        owner = _require_canonical_player(owner_id)
        commander = Commander.objects.filter(pk=commander_id).first()
        if commander is None:
            raise NotFound(f"Commander not found: {commander_id}")

        rows = _parse_export_to_rows(export_text, commander.name)

        moxfield_url = request.data.get("moxfieldUrl") or None
        moxfield_deck_id = extract_moxfield_deck_id(moxfield_url) if moxfield_url else None

        with transaction.atomic():
            deck = Deck.objects.create(
                owner=owner,
                commander=commander,
                name=request.data.get("name") or None,
                source="moxfield" if moxfield_url else "manual",
                moxfield_deck_id=moxfield_deck_id,
                moxfield_url=moxfield_url,
            )
            replace_deck_cards(deck.id, rows)

        context = _deck_detail_context(commander.id)
        return Response(DeckDetailSerializer(get_deck(deck.id), context=context).data, status=HTTP_201_CREATED)


class DeckDetailView(APIView):
    def get(self, request, id):
        deck = get_deck(id)
        if deck is None:
            raise NotFound(f"Deck not found: {id}")
        context = _deck_detail_context(deck.commander_id)
        return Response(DeckDetailSerializer(deck, context=context).data)

    def delete(self, request, id):
        deck = Deck.objects.filter(pk=id).first()
        if deck is None:
            raise NotFound(f"Deck not found: {id}")
        deck.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class DeckArchetypeStatsView(APIView):
    def get(self, request, id):
        if not Deck.objects.filter(pk=id).exists():
            raise NotFound(f"Deck not found: {id}")

        counts = get_deck_role_counts(id)
        targets = {
            "ramp": settings.DECK_TARGET_RAMP,
            "draw": settings.DECK_TARGET_DRAW,
            "removal": settings.DECK_TARGET_REMOVAL,
            "land": settings.DECK_TARGET_LANDS,
        }
        return Response(
            {
                role: {"count": counts[role], "target": target, "met": counts[role] >= target}
                for role, target in targets.items()
            }
        )


class DeckCardsView(APIView):
    def put(self, request, id):
        deck = Deck.objects.select_related("commander").filter(pk=id).first()
        if deck is None:
            raise NotFound(f"Deck not found: {id}")
        export_text = request.data.get("exportText")
        if not export_text:
            raise ValidationError("Body must include exportText")

        rows = _parse_export_to_rows(export_text, deck.commander.name)
        replace_deck_cards(deck.id, rows)

        context = _deck_detail_context(deck.commander_id)
        return Response(DeckDetailSerializer(get_deck(deck.id), context=context).data)
