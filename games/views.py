from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from players.services import get_family_ids, resolve_canonical_player

from .models import Game
from .serializers import GamePlayerDetailSerializer, GameSerializer
from .services import GameListFilters, get_game_player_details, list_games


class GameListView(ListAPIView):
    serializer_class = GameSerializer

    def get_queryset(self):
        q = self.request.query_params
        player_family_ids = None
        player = q.get("player")
        if player:
            canonical = resolve_canonical_player(player)
            if canonical is None:
                raise ValidationError(f"Unknown player: {player}")
            player_family_ids = get_family_ids(canonical.id)

        year = q.get("year")
        parsed_year = None
        if year is not None:
            try:
                parsed_year = int(year)
            except ValueError:
                raise ValidationError(f"Invalid year: {year}")

        def parse_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        filters = GameListFilters(
            player_family_ids=player_family_ids,
            year=parsed_year,
            from_date=q.get("from"),
            to_date=q.get("to"),
            limit=parse_int(q.get("limit")),
            offset=parse_int(q.get("offset")),
        )
        return list_games(filters)


class GameDetailView(APIView):
    def get(self, request, id):
        game = Game.objects.filter(pk=id).first()
        if game is None:
            raise NotFound(f"Game not found: {id}")
        data = GameSerializer(game).data
        players = get_game_player_details(game.id)
        data["players"] = GamePlayerDetailSerializer(players, many=True).data
        return Response(data)
