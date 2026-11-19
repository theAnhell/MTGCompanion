import uuid
from datetime import datetime

from django.test import TestCase

from commanders.models import Commander
from games.models import Game, GamePlayer
from games.services import EnrichedGamePlayerFilters, GameListFilters, list_enriched_game_players, list_games
from players.models import Player


class GamesServiceTests(TestCase):
    def setUp(self):
        self.player_a = Player.objects.create(id=uuid.uuid4(), name="Alice")
        self.player_b = Player.objects.create(id=uuid.uuid4(), name="Bob")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")

        self.game_2025 = Game.objects.create(
            id=uuid.uuid4(), name="2025 Game", created_on=datetime(2025, 6, 1, 12, 0, 0)
        )
        self.game_2026 = Game.objects.create(
            id=uuid.uuid4(), name="2026 Game", created_on=datetime(2026, 6, 1, 12, 0, 0)
        )
        GamePlayer.objects.create(
            id=uuid.uuid4(), game=self.game_2025, player=self.player_a, commander=self.commander, is_winner=True
        )
        GamePlayer.objects.create(
            id=uuid.uuid4(), game=self.game_2026, player=self.player_b, commander=self.commander, is_winner=False
        )

    def test_list_games_filters_by_year(self):
        results = list(list_games(GameListFilters(year=2026)))
        self.assertEqual([g.id for g in results], [self.game_2026.id])

    def test_list_games_filters_by_player_family(self):
        results = list(list_games(GameListFilters(player_family_ids=[self.player_a.id])))
        self.assertEqual([g.id for g in results], [self.game_2025.id])

    def test_list_games_respects_limit_and_offset(self):
        results = list(list_games(GameListFilters(limit=1)))
        self.assertEqual(len(results), 1)

    def test_list_games_no_filters_returns_all_ordered_desc(self):
        results = list(list_games(GameListFilters()))
        self.assertEqual([g.id for g in results], [self.game_2026.id, self.game_2025.id])

    def test_list_enriched_game_players_filters_by_family(self):
        rows = list(list_enriched_game_players(EnrichedGamePlayerFilters(player_family_ids=[self.player_b.id])))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].player_id, self.player_b.id)

    def test_list_enriched_game_players_filters_by_year(self):
        rows = list(list_enriched_game_players(EnrichedGamePlayerFilters(year=2025)))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].game_id, self.game_2025.id)

    def test_list_enriched_game_players_no_filters_returns_all(self):
        rows = list(list_enriched_game_players())
        self.assertEqual(len(rows), 2)
