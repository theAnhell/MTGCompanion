from datetime import datetime

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from players.services import resolve_canonical_player

from .services import (
    get_fastest_to_win_decks,
    get_least_played_decks,
    get_longest_since_played_decks,
    get_player_decks,
    get_player_streaks,
    get_slowest_to_win_decks,
    get_yearly_summary,
)


def _parse_bool(value, fallback: bool) -> bool:
    if value is None:
        return fallback
    return value in ("true", "1")


def _parse_int(value, fallback: int) -> int:
    try:
        n = int(value)
        return n if n > 0 else fallback
    except (TypeError, ValueError):
        return fallback


def _parse_metric(value) -> str:
    return "turns" if value == "turns" else "minutes"


def _require_canonical_player(identifier):
    player = resolve_canonical_player(identifier)
    if player is None:
        raise NotFound(f"Player not found: {identifier}")
    return player


def _deck_query(request) -> dict:
    q = request.query_params
    return {
        "limit": _parse_int(q.get("limit"), 10),
        "wins_min": _parse_int(q.get("winsMin"), 1),
        "metric": _parse_metric(q.get("metric")),
    }


class PlayerDecksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        include_retired = _parse_bool(request.query_params.get("includeRetired"), True)
        return Response(get_player_decks(player.id, include_retired))


class PlayerLeastPlayedDecksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        q = _deck_query(request)
        include_retired = _parse_bool(request.query_params.get("includeRetired"), False)
        return Response(get_least_played_decks(player.id, limit=q["limit"], include_retired=include_retired))


class PlayerLongestSincePlayedDecksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        q = _deck_query(request)
        include_retired = _parse_bool(request.query_params.get("includeRetired"), False)
        return Response(
            get_longest_since_played_decks(player.id, limit=q["limit"], include_retired=include_retired)
        )


class PlayerFastestToWinDecksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        q = _deck_query(request)
        include_retired = _parse_bool(request.query_params.get("includeRetired"), False)
        return Response(
            get_fastest_to_win_decks(
                player.id, metric=q["metric"], wins_min=q["wins_min"], limit=q["limit"], include_retired=include_retired
            )
        )


class PlayerSlowestToWinDecksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        q = _deck_query(request)
        include_retired = _parse_bool(request.query_params.get("includeRetired"), False)
        return Response(
            get_slowest_to_win_decks(
                player.id, metric=q["metric"], wins_min=q["wins_min"], limit=q["limit"], include_retired=include_retired
            )
        )


class PlayerStreaksView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        include_retired = _parse_bool(request.query_params.get("includeRetired"), True)
        return Response(get_player_streaks(player.id, include_retired))


class PlayerSummaryView(APIView):
    def get(self, request, id):
        player = _require_canonical_player(id)
        q = _deck_query(request)
        historical = _parse_bool(request.query_params.get("includeRetired"), True)
        pick_helpers = _parse_bool(request.query_params.get("includeRetired"), False)
        return Response(
            {
                "decks": get_player_decks(player.id, historical),
                "leastPlayed": get_least_played_decks(player.id, limit=q["limit"], include_retired=pick_helpers),
                "longestSincePlayed": get_longest_since_played_decks(
                    player.id, limit=q["limit"], include_retired=pick_helpers
                ),
                "fastestToWin": get_fastest_to_win_decks(
                    player.id, metric=q["metric"], wins_min=q["wins_min"], limit=q["limit"], include_retired=pick_helpers
                ),
                "slowestToWin": get_slowest_to_win_decks(
                    player.id, metric=q["metric"], wins_min=q["wins_min"], limit=q["limit"], include_retired=pick_helpers
                ),
                "streaks": get_player_streaks(player.id, historical),
            }
        )


class YearlyReportView(APIView):
    def get(self, request):
        q = request.query_params
        year_param = q.get("year")
        if year_param:
            try:
                year = int(year_param)
            except ValueError:
                raise ValidationError(f"Invalid year: {year_param}")
        else:
            year = datetime.now().year - 1

        summary = get_yearly_summary(
            year,
            include_retired=_parse_bool(q.get("includeRetired"), True),
            top=_parse_int(q.get("top"), 10),
            min_games=_parse_int(q.get("minGames"), 5),
            wins_min=_parse_int(q.get("winsMin"), 2),
            metric=_parse_metric(q.get("metric")),
            per_player_commanders=_parse_bool(q.get("perPlayerCommanders"), False),
        )
        return Response(summary)
