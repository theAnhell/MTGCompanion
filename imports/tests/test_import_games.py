import json
import tempfile
import uuid
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from commanders.models import Commander
from games.models import Game, GamePlayer
from players.models import Player


def _commander_dict(id_, name):
    return {"id": id_, "name": name, "colors": ["R"], "edhrecRank": 100, "cmc": 3}


def _player_dict(id_, name):
    return {"id": id_, "friendlyName": name, "username": name.lower(), "isYou": False}


class ImportGamesCommandTests(TestCase):
    def setUp(self):
        self.commander_a = str(uuid.uuid4())
        self.commander_b = str(uuid.uuid4())
        self.player_a = str(uuid.uuid4())
        self.player_b = str(uuid.uuid4())
        self.game_id = str(uuid.uuid4())

        self.games_payload = [
            {
                "id": self.game_id,
                "name": "Test Game",
                "createdOn": "2026-01-01T12:00:00",
                "gameType": 1,
                "totalTurns": 10,
                "gameTimeInMinutes": 45,
                "isPublic": False,
                "players": [
                    {
                        "id": str(uuid.uuid4()),
                        "gameId": "00000000-0000-0000-0000-000000000000",
                        "commander": _commander_dict(self.commander_a, "Queen Marchesa"),
                        "player": _player_dict(self.player_a, "Alice"),
                        "hasPartners": False,
                        "turnOrder": 1,
                        "isWinner": True,
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "gameId": "00000000-0000-0000-0000-000000000000",
                        "commander": _commander_dict(self.commander_b, "The Ur-Dragon"),
                        "player": _player_dict(self.player_b, "Bob"),
                        "hasPartners": False,
                        "turnOrder": 2,
                        "isWinner": False,
                    },
                ],
            }
        ]

        self.tmpdir = tempfile.TemporaryDirectory()
        self.games_path = Path(self.tmpdir.name) / "AllGames.json"
        self.games_path.write_text(json.dumps(self.games_payload))
        self.merges_path = Path(self.tmpdir.name) / "player-merges.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def _run(self):
        with override_settings(GAMES_EXPORT_PATH=str(self.games_path), PLAYER_MERGES_PATH=str(self.merges_path)):
            call_command("import_games")

    def test_imports_games_players_and_commanders(self):
        self._run()

        self.assertEqual(Game.objects.count(), 1)
        self.assertEqual(GamePlayer.objects.count(), 2)
        self.assertEqual(Player.objects.count(), 2)
        self.assertEqual(Commander.objects.count(), 2)

        game = Game.objects.get(pk=self.game_id)
        self.assertEqual(game.name, "Test Game")
        self.assertEqual(game.total_turns, 10)

        winner = GamePlayer.objects.get(player_id=self.player_a)
        self.assertTrue(winner.is_winner)
        loser = GamePlayer.objects.get(player_id=self.player_b)
        self.assertFalse(loser.is_winner)

    def test_rerun_is_idempotent(self):
        self._run()
        self._run()

        self.assertEqual(Game.objects.count(), 1)
        self.assertEqual(GamePlayer.objects.count(), 2)
        self.assertEqual(Player.objects.count(), 2)

    def test_upsert_updates_changed_fields(self):
        self._run()
        self.games_payload[0]["name"] = "Renamed Game"
        self.games_path.write_text(json.dumps(self.games_payload))

        self._run()

        game = Game.objects.get(pk=self.game_id)
        self.assertEqual(game.name, "Renamed Game")
        self.assertEqual(Game.objects.count(), 1)

    def test_missing_export_file_raises(self):
        from django.core.management.base import CommandError

        with override_settings(
            GAMES_EXPORT_PATH=str(Path(self.tmpdir.name) / "missing.json"),
            PLAYER_MERGES_PATH=str(self.merges_path),
        ):
            with self.assertRaises(CommandError):
                call_command("import_games")

    def test_applies_player_merges(self):
        self._run()
        self.merges_path.write_text(
            json.dumps([{"aliasId": self.player_b, "canonicalId": self.player_a}])
        )

        self._run()

        alias = Player.objects.get(pk=self.player_b)
        self.assertEqual(str(alias.merged_into_id), self.player_a)
