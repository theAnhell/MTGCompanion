from dataclasses import dataclass, field

from .models import Game, GamePlayer


@dataclass
class GameListFilters:
    player_family_ids: list | None = None
    year: int | None = None
    from_date: str | None = None
    to_date: str | None = None
    limit: int | None = None
    offset: int | None = None


def list_games(filters: GameListFilters):
    queryset = Game.objects.all().order_by("-created_on")
    if filters.player_family_ids:
        queryset = queryset.filter(players__player_id__in=filters.player_family_ids).distinct()
    if filters.year:
        queryset = queryset.filter(created_on__year=filters.year)
    if filters.from_date:
        queryset = queryset.filter(created_on__gte=filters.from_date)
    if filters.to_date:
        queryset = queryset.filter(created_on__lte=filters.to_date)
    if filters.offset:
        queryset = queryset[filters.offset :]
    if filters.limit:
        queryset = queryset[: filters.limit]
    return queryset


def get_game_player_details(game_id):
    return (
        GamePlayer.objects.filter(game_id=game_id)
        .select_related("player", "commander", "commander_partner")
        .order_by("turn_order")
    )


@dataclass
class EnrichedGamePlayerFilters:
    player_family_ids: list | None = None
    year: int | None = None


def list_enriched_game_players(filters: EnrichedGamePlayerFilters = field(default_factory=EnrichedGamePlayerFilters)):
    """Joined game_players+games+commanders rows, the shared input for
    streaks/yearly aggregation (mirrors games.repository#listEnrichedGamePlayers)."""
    queryset = (
        GamePlayer.objects.select_related("game", "commander")
        .order_by("game__created_on")
    )
    if filters.player_family_ids:
        queryset = queryset.filter(player_id__in=filters.player_family_ids)
    if filters.year:
        queryset = queryset.filter(game__created_on__year=filters.year)
    return queryset
