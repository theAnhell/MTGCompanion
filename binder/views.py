from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from imports.moxfield_parser import parse_moxfield_export
from players.services import resolve_canonical_player

from .serializers import BinderCardSerializer
from .services import list_binder_cards, replace_binder_cards


def _require_canonical_player(identifier):
    player = resolve_canonical_player(identifier)
    if player is None:
        raise NotFound(f"Player not found: {identifier}")
    return player


class BinderView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        cards = list_binder_cards(player.id)
        return Response(BinderCardSerializer(cards, many=True).data)

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
        cards = list_binder_cards(player.id)
        return Response(BinderCardSerializer(cards, many=True).data)
