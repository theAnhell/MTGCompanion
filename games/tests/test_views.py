import uuid
from datetime import datetime

from rest_framework.test import APITestCase

from commanders.models import Commander
from games.models import Game, GamePlayer
from players.models import Player


class GameListViewTests(APITestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Alice")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.game = Game.objects.create(
            id=uuid.uuid4(), name="Test Game", created_on=datetime(2026, 6, 1, 12, 0, 0, 500000)
        )
        GamePlayer.objects.create(
            id=uuid.uuid4(), game=self.game, player=self.player, commander=self.commander, is_winner=True
        )

    def test_list_all(self):
        response = self.client.get("/api/v1/games")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_created_on_formatted_with_millisecond_precision(self):
        response = self.client.get("/api/v1/games")
        self.assertEqual(response.data[0]["createdOn"], "2026-06-01T12:00:00.500Z")

    def test_filter_by_unknown_player_400s(self):
        response = self.client.get("/api/v1/games?player=NobodyAtAll")
        self.assertEqual(response.status_code, 400)

    def test_filter_by_player_name(self):
        response = self.client.get("/api/v1/games?player=Alice")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_invalid_year_400s(self):
        response = self.client.get("/api/v1/games?year=not-a-year")
        self.assertEqual(response.status_code, 400)


class GameDetailViewTests(APITestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Alice")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.game = Game.objects.create(id=uuid.uuid4(), name="Test Game", created_on=datetime(2026, 6, 1))
        GamePlayer.objects.create(
            id=uuid.uuid4(), game=self.game, player=self.player, commander=self.commander,
            is_winner=True, turn_order=1,
        )

    def test_get_includes_players(self):
        response = self.client.get(f"/api/v1/games/{self.game.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["players"]), 1)
        self.assertEqual(response.data["players"][0]["playerName"], "Alice")
        self.assertIsNone(response.data["players"][0]["commanderPartnerName"])

    def test_get_missing_game_404s(self):
        response = self.client.get(f"/api/v1/games/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)
