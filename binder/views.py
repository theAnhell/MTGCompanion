from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.models import Card
from imports.moxfield_parser import parse_moxfield_export
from players.services import resolve_canonical_player

from .serializers import BinderCardSerializer
from .services import list_binder_cards, replace_binder_cards


def _require_canonical_player(identifier):
    player = resolve_canonical_player(identifier)
    if player is None:
        raise NotFound(f"Player not found: {identifier}")
    return player


def _scryfall_id_context(cards) -> dict:
    card_names = [c.card_name for c in cards]
    return {"scryfall_ids_by_name": dict(Card.objects.filter(name__in=card_names).values_list("name", "scryfall_id"))}


class BinderView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        cards = list(list_binder_cards(player.id))
        context = _scryfall_id_context(cards)
        return Response(BinderCardSerializer(cards, many=True, context=context).data)

    def put(self, request, id):
        player = _require_canonical_player(id)
        export_text = request.data.get("exportText")
        if not export_text:
            raise ValidationError("Body must include exportText")

        parsed = parse_moxfield_export(export_text)
        if not parsed:
            raise ValidationError("No cards could be parsed from exportText")
        rows = [
            {
                "card_name": card["cardName"],
                "set_code": card["setCode"],
                "collector_number": card["collectorNumber"],
                "quantity": card["quantity"],
                "is_foil": card["isFoil"],
            }
            for card in parsed
        ]

        replace_binder_cards(player.id, rows)
        cards = list(list_binder_cards(player.id))
        context = _scryfall_id_context(cards)
        return Response(BinderCardSerializer(cards, many=True, context=context).data)
