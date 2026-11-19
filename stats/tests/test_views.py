import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from commanders.models import Commander
from games.models import Game, GamePlayer
from players.models import Player


class StatsViewsTestCase(APITestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Alice")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        now = timezone.now().replace(month=6, day=15)
        game = Game.objects.create(
            id=uuid.uuid4(), name="Game", created_on=now - timedelta(days=1),
            total_turns=10, game_time_in_minutes=40,
        )
        GamePlayer.objects.create(
            id=uuid.uuid4(), game=game, player=self.player, commander=self.commander, is_winner=True
        )


class PlayerDecksViewTests(StatsViewsTestCase):
    def test_returns_decks(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/decks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_unknown_player_404s(self):
        response = self.client.get(f"/api/v1/players/{uuid.uuid4()}/decks")
        self.assertEqual(response.status_code, 404)


class PlayerLeastPlayedDecksViewTests(StatsViewsTestCase):
    def test_returns_results(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/decks/least-played")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_limit_respected(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/decks/least-played?limit=0")
        # limit=0 falls back to the default (10) rather than returning nothing.
        self.assertEqual(response.status_code, 200)


class PlayerFastestSlowestToWinViewTests(StatsViewsTestCase):
    def test_fastest_to_win(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/decks/fastest-to-win")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["avg"], 40)

    def test_slowest_to_win_with_turns_metric(self):
        response = self.client.get(
            f"/api/v1/players/{self.player.id}/decks/slowest-to-win?metric=turns"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["unit"], "turns")


class PlayerStreaksViewTests(StatsViewsTestCase):
    def test_returns_streaks(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/streaks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["longestWinStreak"]["length"], 1)


class PlayerSummaryViewTests(StatsViewsTestCase):
    def test_returns_full_summary_shape(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/summary")
        self.assertEqual(response.status_code, 200)
        for key in ["decks", "leastPlayed", "longestSincePlayed", "fastestToWin", "slowestToWin", "streaks"]:
            self.assertIn(key, response.data)


class YearlyReportViewTests(StatsViewsTestCase):
    def test_defaults_to_last_year_when_omitted(self):
        response = self.client.get("/api/v1/reports/yearly")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["year"], timezone.now().year - 1)

    def test_returns_summary_for_year(self):
        year = timezone.now().year
        response = self.client.get(f"/api/v1/reports/yearly?year={year}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["year"], year)
        self.assertGreaterEqual(response.data["totalGames"], 1)

    def test_invalid_year_400s(self):
        response = self.client.get("/api/v1/reports/yearly?year=not-a-year")
        self.assertEqual(response.status_code, 400)
