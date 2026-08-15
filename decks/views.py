from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from commanders.models import Commander
from players.services import get_family_ids, resolve_canonical_player

from .serializers import RetiredDeckSerializer
from .services import add_retired_deck, list_retired_decks_with_commander_info, remove_retired_deck


def _require_canonical_player(identifier):
    player = resolve_canonical_player(identifier)
    if player is None:
        raise NotFound(f"Player not found: {identifier}")
    return player


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
