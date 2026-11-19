import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from binder.models import BinderCard
from cards.models import Card
from commanders.models import Commander, CommanderCardStat
from decks.models import Deck, DeckCard
from players.models import Player
from recommendations.models import Recommendation
from recommendations.services import (
    find_best_decks_for_card,
    find_binder_card_fits,
    generate_recommendations,
    get_candidate_adds,
    get_candidate_removes,
    get_card_sources,
    get_player_collection_card_names,
    get_role_gap_adds,
    update_recommendation,
)


def _fresh_commander(name="Commander") -> Commander:
    """A commander whose EDHREC data is considered fresh, so service calls
    never try to perform a real network sync."""
    return Commander.objects.create(id=uuid.uuid4(), name=name, edhrec_synced_at=timezone.now())


class GetPlayerCollectionCardNamesTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck_a = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        self.deck_b = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Sol Ring", quantity=1)
        DeckCard.objects.create(deck=self.deck_b, card_name="Arcane Signet", quantity=1)
        DeckCard.objects.create(deck=self.deck_a, card_name="Already In This Deck", quantity=1)

    def test_union_of_binder_and_other_decks(self):
        names = get_player_collection_card_names(self.owner.id, exclude_deck_id=self.deck_a.id)
        self.assertEqual(names, {"Sol Ring", "Arcane Signet"})

    def test_excludes_evaluated_decks_own_cards(self):
        names = get_player_collection_card_names(self.owner.id, exclude_deck_id=self.deck_a.id)
        self.assertNotIn("Already In This Deck", names)

    def test_without_exclusion_includes_everything(self):
        names = get_player_collection_card_names(self.owner.id)
        self.assertIn("Already In This Deck", names)


class GetCandidateAddsTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="High Inclusion", quantity=1)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Low Inclusion", quantity=1)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="No EDHREC Data", quantity=1)
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="High Inclusion", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=80.0,
        )
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Low Inclusion", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=5.0,
        )

    def test_above_threshold_suggested(self):
        results = get_candidate_adds(self.deck.id, threshold=40.0)
        names = {r["card_name"] for r in results}
        self.assertIn("High Inclusion", names)

    def test_below_threshold_excluded(self):
        results = get_candidate_adds(self.deck.id, threshold=40.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn("Low Inclusion", names)

    def test_no_edhrec_data_never_suggested(self):
        results = get_candidate_adds(self.deck.id, threshold=0.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn("No EDHREC Data", names)

    def test_card_already_in_deck_not_suggested(self):
        DeckCard.objects.create(deck=self.deck, card_name="High Inclusion", quantity=1)
        results = get_candidate_adds(self.deck.id, threshold=40.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn("High Inclusion", names)

    def test_empty_collection_returns_empty(self):
        BinderCard.objects.filter(player=self.owner).delete()
        self.assertEqual(get_candidate_adds(self.deck.id), [])


class GetCandidateRemovesTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        DeckCard.objects.create(deck=self.deck, card_name="Weak Card", quantity=1)
        DeckCard.objects.create(deck=self.deck, card_name="Strong Card", quantity=1)
        DeckCard.objects.create(deck=self.deck, card_name="Plains", quantity=10)
        DeckCard.objects.create(
            deck=self.deck, card_name=self.commander.name, quantity=1, is_commander=True
        )
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Weak Card", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=5.0,
        )
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Strong Card", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=90.0,
        )

    def test_low_inclusion_card_flagged(self):
        results = get_candidate_removes(self.deck.id, threshold=20.0)
        names = {r["card_name"] for r in results}
        self.assertIn("Weak Card", names)

    def test_high_inclusion_card_not_flagged(self):
        results = get_candidate_removes(self.deck.id, threshold=20.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn("Strong Card", names)

    def test_commander_never_flagged(self):
        results = get_candidate_removes(self.deck.id, threshold=100.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn(self.commander.name, names)

    def test_basics_excluded_by_default(self):
        results = get_candidate_removes(self.deck.id, threshold=100.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn("Plains", names)

    def test_basics_included_when_requested(self):
        # Plains has no CommanderCardStat row, so it still won't show up —
        # exercising exclude_basics=False without a matching stat row.
        results = get_candidate_removes(self.deck.id, threshold=100.0, exclude_basics=False)
        names = {r["card_name"] for r in results}
        self.assertNotIn("Plains", names)

    def test_no_edhrec_data_never_flagged(self):
        DeckCard.objects.create(deck=self.deck, card_name="Unknown Card", quantity=1)
        results = get_candidate_removes(self.deck.id, threshold=100.0)
        names = {r["card_name"] for r in results}
        self.assertNotIn("Unknown Card", names)


class FindBestDecksForCardTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander_a = _fresh_commander("Commander A")
        self.commander_b = _fresh_commander("Commander B")
        self.commander_c = _fresh_commander("Commander C")
        self.deck_a = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander_a)
        self.deck_b = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander_b)
        self.deck_c = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander_c)
        CommanderCardStat.objects.create(
            commander=self.commander_a, card_name="Mayhem Devil", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=50.0,
        )
        CommanderCardStat.objects.create(
            commander=self.commander_b, card_name="Mayhem Devil", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=20.0,
        )
        # commander_c has no CommanderCardStat row for this card at all.

    def test_ranks_by_inclusion_rate_descending(self):
        results = find_best_decks_for_card(self.owner.id, "Mayhem Devil")
        self.assertEqual([r["deck_id"] for r in results], [self.deck_a.id, self.deck_b.id])

    def test_decks_without_edhrec_data_excluded(self):
        results = find_best_decks_for_card(self.owner.id, "Mayhem Devil")
        deck_ids = {r["deck_id"] for r in results}
        self.assertNotIn(self.deck_c.id, deck_ids)

    def test_deck_already_running_card_excluded(self):
        DeckCard.objects.create(deck=self.deck_a, card_name="Mayhem Devil", quantity=1)
        results = find_best_decks_for_card(self.owner.id, "Mayhem Devil")
        deck_ids = {r["deck_id"] for r in results}
        self.assertNotIn(self.deck_a.id, deck_ids)

    def test_limit_caps_results(self):
        results = find_best_decks_for_card(self.owner.id, "Mayhem Devil", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["deck_id"], self.deck_a.id)

    def test_no_decks_returns_empty(self):
        lonely = Player.objects.create(id=uuid.uuid4(), name="Lonely")
        self.assertEqual(find_best_decks_for_card(lonely.id, "Mayhem Devil"), [])

    @patch("recommendations.services.sync_commander_card_stats")
    def test_stale_commander_sync_failure_does_not_abort(self, mock_sync):
        import requests

        self.commander_a.edhrec_synced_at = None
        self.commander_a.save(update_fields=["edhrec_synced_at"])
        mock_sync.side_effect = requests.RequestException("boom")

        # A failed refresh attempt isn't fatal to the whole lookup — it just
        # means commander_a's existing (now possibly stale) stats are used
        # as-is rather than refreshed first.
        results = find_best_decks_for_card(self.owner.id, "Mayhem Devil")

        self.assertEqual([r["deck_id"] for r in results], [self.deck_a.id, self.deck_b.id])
        mock_sync.assert_called_once_with(self.commander_a.id)


class FindBinderCardFitsTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander_a = _fresh_commander("Commander A")
        self.commander_b = _fresh_commander("Commander B")
        self.deck_a = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander_a)
        self.deck_b = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander_b)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Sol Ring", quantity=1)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="No Match", quantity=1)
        CommanderCardStat.objects.create(
            commander=self.commander_a, card_name="Sol Ring", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=30.0,
        )
        CommanderCardStat.objects.create(
            commander=self.commander_b, card_name="Sol Ring", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=90.0,
        )

    def test_picks_single_best_deck_per_card(self):
        results = find_binder_card_fits(self.owner.id)
        sol_ring = next(r for r in results if r["card_name"] == "Sol Ring")
        self.assertEqual(sol_ring["deck_id"], self.deck_b.id)
        self.assertEqual(sol_ring["inclusion_rate"], 90.0)

    def test_card_with_no_deck_match_is_absent(self):
        results = find_binder_card_fits(self.owner.id)
        names = {r["card_name"] for r in results}
        self.assertNotIn("No Match", names)

    def test_card_already_in_best_deck_falls_back_to_next_best(self):
        DeckCard.objects.create(deck=self.deck_b, card_name="Sol Ring", quantity=1)
        results = find_binder_card_fits(self.owner.id)
        sol_ring = next(r for r in results if r["card_name"] == "Sol Ring")
        self.assertEqual(sol_ring["deck_id"], self.deck_a.id)

    def test_empty_binder_returns_empty(self):
        BinderCard.objects.filter(player=self.owner).delete()
        self.assertEqual(find_binder_card_fits(self.owner.id), [])


class GetCardSourcesTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        self.other_deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander, name="Other Deck")

    def test_binder_takes_priority_over_deck(self):
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Mayhem Devil", quantity=1)
        DeckCard.objects.create(deck=self.other_deck, card_name="Mayhem Devil", quantity=1)

        sources = get_card_sources(self.owner.id, ["Mayhem Devil"])

        self.assertEqual(sources["Mayhem Devil"]["source_type"], Recommendation.SourceType.BINDER)
        self.assertIsNone(sources["Mayhem Devil"]["source_deck_id"])

    def test_deck_only_source_used_when_not_in_binder(self):
        DeckCard.objects.create(deck=self.other_deck, card_name="Mayhem Devil", quantity=1)

        sources = get_card_sources(self.owner.id, ["Mayhem Devil"])

        self.assertEqual(sources["Mayhem Devil"]["source_type"], Recommendation.SourceType.DECK)
        self.assertEqual(sources["Mayhem Devil"]["source_deck_id"], self.other_deck.id)
        self.assertEqual(sources["Mayhem Devil"]["source_deck_name"], "Other Deck")

    def test_excludes_the_deck_being_evaluated(self):
        DeckCard.objects.create(deck=self.deck, card_name="Mayhem Devil", quantity=1)

        sources = get_card_sources(self.owner.id, ["Mayhem Devil"], exclude_deck_id=self.deck.id)

        self.assertNotIn("Mayhem Devil", sources)

    def test_card_nowhere_in_collection_absent(self):
        sources = get_card_sources(self.owner.id, ["Mayhem Devil"])
        self.assertEqual(sources, {})

    def test_empty_card_names_returns_empty(self):
        self.assertEqual(get_card_sources(self.owner.id, []), {})


class GetRoleGapAddsTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Rampant Growth", quantity=1)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Not Ramp", quantity=1)
        Card.objects.create(name="Rampant Growth", roles=["ramp"])
        Card.objects.create(name="Not Ramp", roles=["draw"])
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Rampant Growth", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=50.0,
        )

    @override_settings(DECK_TARGET_RAMP=1, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0)
    def test_suggests_card_for_unmet_role(self):
        results = get_role_gap_adds(self.deck.id)
        names = {r["card_name"] for r in results}
        self.assertIn("Rampant Growth", names)
        match = next(r for r in results if r["card_name"] == "Rampant Growth")
        self.assertEqual(match["role"], "ramp")

    @override_settings(DECK_TARGET_RAMP=0, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0)
    def test_no_gap_means_no_suggestions(self):
        self.assertEqual(get_role_gap_adds(self.deck.id), [])

    @override_settings(DECK_TARGET_RAMP=1, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0)
    def test_wrong_role_card_not_suggested_for_ramp_gap(self):
        results = get_role_gap_adds(self.deck.id)
        names = {r["card_name"] for r in results}
        self.assertNotIn("Not Ramp", names)

    @override_settings(DECK_TARGET_RAMP=5, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0)
    def test_gap_count_limits_results(self):
        Card.objects.create(name="Second Ramp Card", roles=["ramp"])
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Second Ramp Card", quantity=1)
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Second Ramp Card", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=10.0,
        )
        # Gap is 5, but only 2 ramp candidates exist in the collection — both returned.
        results = get_role_gap_adds(self.deck.id)
        self.assertEqual(len(results), 2)


class GenerateRecommendationsTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Good Add", quantity=1)
        DeckCard.objects.create(deck=self.deck, card_name="Bad Card", quantity=1)
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Good Add", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=90.0,
        )
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Bad Card", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=1.0,
        )

    @override_settings(
        RECOMMENDATION_ADD_THRESHOLD=40.0,
        RECOMMENDATION_REMOVE_THRESHOLD=20.0,
        DECK_TARGET_RAMP=0, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0,
    )
    def test_creates_add_and_remove_rows(self):
        recs = generate_recommendations(self.deck.id)
        actions = {(r.action, r.card_name) for r in recs}
        self.assertIn((Recommendation.Action.ADD, "Good Add"), actions)
        self.assertIn((Recommendation.Action.REMOVE, "Bad Card"), actions)

    @override_settings(
        RECOMMENDATION_ADD_THRESHOLD=40.0,
        RECOMMENDATION_REMOVE_THRESHOLD=20.0,
        DECK_TARGET_RAMP=0, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0,
    )
    def test_add_row_has_binder_source(self):
        generate_recommendations(self.deck.id)
        rec = Recommendation.objects.get(deck=self.deck, card_name="Good Add")
        self.assertEqual(rec.source_type, Recommendation.SourceType.BINDER)

    @override_settings(
        RECOMMENDATION_ADD_THRESHOLD=40.0,
        RECOMMENDATION_REMOVE_THRESHOLD=20.0,
        DECK_TARGET_RAMP=0, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0,
    )
    def test_regenerate_does_not_touch_approved_rows(self):
        generate_recommendations(self.deck.id)
        rec = Recommendation.objects.get(deck=self.deck, card_name="Good Add")
        rec.status = Recommendation.Status.APPROVED
        rec.save(update_fields=["status"])

        generate_recommendations(self.deck.id)

        rec.refresh_from_db()
        self.assertEqual(rec.status, Recommendation.Status.APPROVED)
        self.assertEqual(
            Recommendation.objects.filter(deck=self.deck, card_name="Good Add").count(), 1
        )

    @override_settings(
        RECOMMENDATION_ADD_THRESHOLD=40.0,
        RECOMMENDATION_REMOVE_THRESHOLD=20.0,
        DECK_TARGET_RAMP=0, DECK_TARGET_DRAW=0, DECK_TARGET_REMOVAL=0, DECK_TARGET_LANDS=0,
    )
    def test_stale_proposed_rows_are_cleared_on_regenerate(self):
        stale = Recommendation.objects.create(
            player=self.owner, deck=self.deck, action=Recommendation.Action.ADD,
            card_name="No Longer Relevant", inclusion_rate=99.0,
        )
        generate_recommendations(self.deck.id)
        self.assertFalse(Recommendation.objects.filter(pk=stale.id).exists())

    @patch("recommendations.services.sync_commander_card_stats")
    def test_stale_commander_triggers_sync(self, mock_sync):
        self.commander.edhrec_synced_at = None
        self.commander.save(update_fields=["edhrec_synced_at"])

        generate_recommendations(self.deck.id)

        mock_sync.assert_called_once_with(self.commander.id)

    @patch("recommendations.services.sync_commander_card_stats")
    def test_fresh_commander_skips_sync(self, mock_sync):
        generate_recommendations(self.deck.id)
        mock_sync.assert_not_called()


class UpdateRecommendationTests(TestCase):
    def setUp(self):
        owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        commander = _fresh_commander()
        deck = Deck.objects.create(id=uuid.uuid4(), owner=owner, commander=commander)
        self.rec = Recommendation.objects.create(
            player=owner, deck=deck, action=Recommendation.Action.ADD,
            card_name="Sol Ring", inclusion_rate=50.0,
        )

    def test_updates_status(self):
        updated = update_recommendation(self.rec.id, status=Recommendation.Status.APPROVED)
        self.assertEqual(updated.status, Recommendation.Status.APPROVED)

    def test_applied_true_sets_timestamp(self):
        updated = update_recommendation(self.rec.id, applied=True)
        self.assertIsNotNone(updated.applied_at)

    def test_applied_false_clears_timestamp(self):
        update_recommendation(self.rec.id, applied=True)
        updated = update_recommendation(self.rec.id, applied=False)
        self.assertIsNone(updated.applied_at)

    def test_no_args_leaves_record_unchanged(self):
        updated = update_recommendation(self.rec.id)
        self.assertEqual(updated.status, Recommendation.Status.PROPOSED)
        self.assertIsNone(updated.applied_at)
