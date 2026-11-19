import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from commanders.models import Commander
from decks.models import RetiredDeck
from games.models import Game, GamePlayer
from players.models import Player
from stats.services import (
    compute_streaks_from_events,
    get_fastest_to_win_decks,
    get_least_played_decks,
    get_longest_since_played_decks,
    get_player_decks,
    get_player_streaks,
    get_slowest_to_win_decks,
    get_yearly_summary,
)


class ComputeStreaksFromEventsTests(TestCase):
    def test_no_events_returns_zeroed_streaks(self):
        result = compute_streaks_from_events([])
        self.assertEqual(result["longestWinStreak"]["length"], 0)
        self.assertEqual(result["longestLossStreak"]["length"], 0)

    def test_all_wins_is_one_streak(self):
        base = timezone.now()
        events = [{"date": base + timedelta(days=i), "win": True} for i in range(3)]
        result = compute_streaks_from_events(events)
        self.assertEqual(result["longestWinStreak"]["length"], 3)
        self.assertEqual(result["longestLossStreak"]["length"], 0)

    def test_mixed_results_finds_longest_streak_of_each_type(self):
        base = timezone.now()
        # W L L L W W
        wins = [True, False, False, False, True, True]
        events = [{"date": base + timedelta(days=i), "win": w} for i, w in enumerate(wins)]
        result = compute_streaks_from_events(events)
        self.assertEqual(result["longestWinStreak"]["length"], 2)
        self.assertEqual(result["longestLossStreak"]["length"], 3)

    def test_events_sorted_by_date_before_computing(self):
        base = timezone.now()
        # Provided out of order; the loss streak comes first chronologically.
        events = [
            {"date": base + timedelta(days=2), "win": True},
            {"date": base, "win": False},
            {"date": base + timedelta(days=1), "win": False},
        ]
        result = compute_streaks_from_events(events)
        self.assertEqual(result["longestLossStreak"]["length"], 2)
        self.assertEqual(result["longestWinStreak"]["length"], 1)


class StatsFixtureTestCase(TestCase):
    """Shared fixture: Alice and Bob have each piloted two commanders across
    several games, with enough spread in dates/results to exercise ranking,
    streak, and speed logic."""

    def setUp(self):
        self.alice = Player.objects.create(id=uuid.uuid4(), name="Alice")
        self.bob = Player.objects.create(id=uuid.uuid4(), name="Bob")

        self.marchesa = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa", edhrec_rank=10)
        self.ur_dragon = Commander.objects.create(id=uuid.uuid4(), name="The Ur-Dragon", edhrec_rank=20)
        self.retired_commander = Commander.objects.create(id=uuid.uuid4(), name="Retired One")

        # Anchored mid-year (not "now") so every date below stays safely
        # within the same calendar year regardless of when the suite runs —
        # a raw `now - timedelta(days=200)` could cross a Jan/Dec boundary
        # and make the yearly-summary assertions flaky.
        anchor = timezone.now().replace(month=6, day=15, hour=12, minute=0, second=0, microsecond=0)

        # Alice: 3 games on Marchesa (2 wins, fast; 1 loss), 1 game on
        # Retired One in a clearly different year (retired for her specifically).
        self._play(self.alice, self.marchesa, anchor - timedelta(days=30), won=True, minutes=40, turns=8)
        self._play(self.alice, self.marchesa, anchor - timedelta(days=20), won=True, minutes=30, turns=6)
        self._play(self.alice, self.marchesa, anchor - timedelta(days=1), won=False, minutes=60, turns=12)
        self._play(
            self.alice, self.retired_commander, anchor.replace(year=anchor.year - 1),
            won=True, minutes=50, turns=10,
        )

        # Bob: 2 games on Ur-Dragon, both wins, slower.
        self._play(self.bob, self.ur_dragon, anchor - timedelta(days=15), won=True, minutes=90, turns=15)
        self._play(self.bob, self.ur_dragon, anchor - timedelta(days=5), won=True, minutes=100, turns=16)

        RetiredDeck.objects.create(player=self.alice, commander=self.retired_commander)

    def _play(self, player, commander, created_on, *, won, minutes, turns):
        game = Game.objects.create(
            id=uuid.uuid4(), name="Game", created_on=created_on,
            game_time_in_minutes=minutes, total_turns=turns,
        )
        GamePlayer.objects.create(
            id=uuid.uuid4(), game=game, player=player, commander=commander, is_winner=won,
        )
        return game


class GetPlayerDecksTests(StatsFixtureTestCase):
    def test_excludes_retired_by_default(self):
        decks = get_player_decks(self.alice.id)
        names = {d["commanderName"] for d in decks}
        self.assertNotIn("Retired One", names)

    def test_includes_retired_when_requested(self):
        decks = get_player_decks(self.alice.id, include_retired=True)
        names = {d["commanderName"] for d in decks}
        self.assertIn("Retired One", names)

    def test_retired_flag_set_correctly(self):
        decks = get_player_decks(self.alice.id, include_retired=True)
        retired = next(d for d in decks if d["commanderName"] == "Retired One")
        active = next(d for d in decks if d["commanderName"] == "Queen Marchesa")
        self.assertTrue(retired["retired"])
        self.assertFalse(active["retired"])

    def test_win_rate_and_games_played(self):
        decks = get_player_decks(self.alice.id, include_retired=False)
        marchesa = decks[0]
        self.assertEqual(marchesa["gamesPlayed"], 3)
        self.assertEqual(marchesa["wins"], 2)
        self.assertAlmostEqual(marchesa["winRate"], 66.7, places=1)

    def test_scoped_to_player(self):
        decks = get_player_decks(self.bob.id)
        self.assertEqual(len(decks), 1)
        self.assertEqual(decks[0]["commanderName"], "The Ur-Dragon")


class LeastPlayedAndLongestSincePlayedTests(StatsFixtureTestCase):
    def test_least_played_sorts_fewest_games_first(self):
        results = get_least_played_decks(self.alice.id, include_retired=True)
        self.assertEqual(results[0]["commanderName"], "Retired One")

    def test_longest_since_played_excludes_never_played(self):
        results = get_longest_since_played_decks(self.alice.id, include_retired=True)
        names = [r["commanderName"] for r in results]
        self.assertIn("Retired One", names)
        self.assertEqual(results[0]["commanderName"], "Retired One")

    def test_limit_is_respected(self):
        results = get_least_played_decks(self.alice.id, limit=1, include_retired=True)
        self.assertEqual(len(results), 1)


class SpeedRankingTests(StatsFixtureTestCase):
    def test_fastest_to_win_uses_only_wins(self):
        results = get_fastest_to_win_decks(self.alice.id, metric="minutes", wins_min=1, include_retired=False)
        self.assertEqual(results[0]["commanderName"], "Queen Marchesa")
        self.assertEqual(results[0]["wins"], 2)
        self.assertEqual(results[0]["avg"], 35.0)

    def test_slowest_to_win_orders_descending_by_avg(self):
        results = get_slowest_to_win_decks(self.bob.id, metric="minutes", wins_min=1)
        self.assertEqual(results[0]["avg"], 95.0)

    def test_wins_min_filters_out_insufficient_samples(self):
        results = get_fastest_to_win_decks(self.alice.id, metric="minutes", wins_min=5, include_retired=False)
        self.assertEqual(results, [])

    def test_turns_metric(self):
        results = get_fastest_to_win_decks(self.alice.id, metric="turns", wins_min=1, include_retired=False)
        self.assertEqual(results[0]["avg"], 7.0)
        self.assertEqual(results[0]["unit"], "turns")


class GetPlayerStreaksTests(StatsFixtureTestCase):
    def test_alice_has_a_two_game_win_streak(self):
        streaks = get_player_streaks(self.alice.id, include_retired=False)
        self.assertEqual(streaks["longestWinStreak"]["length"], 2)

    def test_bob_has_a_two_game_win_streak_and_no_losses(self):
        streaks = get_player_streaks(self.bob.id)
        self.assertEqual(streaks["longestWinStreak"]["length"], 2)
        self.assertEqual(streaks["longestLossStreak"]["length"], 0)


class GetYearlySummaryTests(StatsFixtureTestCase):
    def test_filters_to_the_given_year(self):
        this_year = timezone.now().year
        summary = get_yearly_summary(this_year)
        self.assertGreaterEqual(summary["totalGames"], 1)

    def test_other_year_has_no_games(self):
        summary = get_yearly_summary(1999)
        self.assertEqual(summary["totalGames"], 0)
        self.assertEqual(summary["uniquePlayers"], 0)

    def test_players_by_wins_includes_both_players(self):
        this_year = timezone.now().year
        summary = get_yearly_summary(this_year, min_games=1)
        names = {p["name"] for p in summary["playersByWins"]}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_commanders_by_most_played(self):
        this_year = timezone.now().year
        summary = get_yearly_summary(this_year)
        top = summary["commandersByMostPlayed"][0]
        self.assertEqual(top["name"], "Queen Marchesa")
        self.assertEqual(top["games"], 3)

    def test_per_player_commanders_breakdown(self):
        this_year = timezone.now().year
        summary = get_yearly_summary(this_year, per_player_commanders=True)
        self.assertIn("perPlayerCommanders", summary)
        alice_decks = summary["perPlayerCommanders"][str(self.alice.id)]["decks"]
        self.assertTrue(any(d["commanderName"] == "Queen Marchesa" for d in alice_decks))

    def test_excludes_retired_decks_by_default(self):
        this_year = timezone.now().year
        summary = get_yearly_summary(this_year)
        names = {c["name"] for c in summary["commandersByMostPlayed"]}
        self.assertNotIn("Retired One", names)
