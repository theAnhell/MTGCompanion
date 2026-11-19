import gzip
import io
import json
import uuid
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from cards.models import Card
from cards.services import classify_roles, get_deck_role_counts, sync_scryfall_cards
from decks.models import Deck, DeckCard
from commanders.models import Commander
from players.models import Player


class ClassifyRolesTests(SimpleTestCase):
    def test_land_type_line(self):
        self.assertEqual(classify_roles("", "Land"), ["land"])

    def test_basic_land_subtype(self):
        self.assertEqual(classify_roles("", "Basic Land — Forest"), ["land"])

    def test_ramp_search_library_pattern(self):
        roles = classify_roles("Search your library for a land card.", "Sorcery")
        self.assertIn("ramp", roles)

    def test_ramp_additional_land_pattern(self):
        roles = classify_roles("You may play an additional land this turn.", "Enchantment")
        self.assertIn("ramp", roles)

    def test_ramp_mana_ability_pattern(self):
        roles = classify_roles("{T}: Add {C}{C}.", "Artifact")
        self.assertIn("ramp", roles)

    def test_mana_ability_does_not_override_land_role(self):
        # A land that taps for mana should just be "land", not also "ramp"
        # via the generic mana-ability pattern.
        roles = classify_roles("{T}: Add {G}.", "Land")
        self.assertEqual(roles, ["land"])

    def test_draw_pattern(self):
        roles = classify_roles("Draw a card.", "Instant")
        self.assertIn("draw", roles)

    def test_draw_numeric_pattern(self):
        roles = classify_roles("Draw two cards.", "Sorcery")
        self.assertIn("draw", roles)

    def test_removal_destroy_target(self):
        roles = classify_roles("Destroy target creature.", "Instant")
        self.assertIn("removal", roles)

    def test_removal_damage_pattern(self):
        roles = classify_roles("Chandra deals 3 damage to any target.", "Sorcery")
        self.assertIn("removal", roles)

    def test_removal_fight_pattern(self):
        roles = classify_roles("Target creature you control fights target creature.", "Sorcery")
        self.assertIn("removal", roles)

    def test_vanilla_creature_has_no_roles(self):
        self.assertEqual(classify_roles("", "Creature — Bear"), [])

    def test_multiple_roles_at_once(self):
        roles = classify_roles(
            "Search your library for a land card. Draw a card. Destroy target artifact.", "Sorcery"
        )
        self.assertEqual(set(roles), {"ramp", "draw", "removal"})

    def test_none_inputs_do_not_crash(self):
        self.assertEqual(classify_roles(None, None), [])


class GetDeckRoleCountsTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        Card.objects.create(name="Rampant Growth", roles=["ramp"])
        Card.objects.create(name="Sign in Blood", roles=["draw"])
        Card.objects.create(name="Swamp", roles=["land"])
        # No Card row for this one at all — must be silently skipped.
        DeckCard.objects.create(deck=self.deck, card_name="Rampant Growth", quantity=1)
        DeckCard.objects.create(deck=self.deck, card_name="Sign in Blood", quantity=1)
        DeckCard.objects.create(deck=self.deck, card_name="Swamp", quantity=5)
        DeckCard.objects.create(deck=self.deck, card_name="Unknown Card", quantity=1)
        DeckCard.objects.create(
            deck=self.deck, card_name="Queen Marchesa", quantity=1, is_commander=True
        )

    def test_counts_by_role_excluding_commander_and_unknown(self):
        counts = get_deck_role_counts(self.deck.id)
        self.assertEqual(counts, {"ramp": 1, "draw": 1, "removal": 0, "land": 5})


class SyncScryfallCardsTests(TestCase):
    def _jsonl_gzip(self, cards: list[dict]) -> bytes:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            for card in cards:
                f.write((json.dumps(card) + "\n").encode())
        return buf.getvalue()

    @patch("cards.services.requests.get")
    def test_syncs_normal_card(self, mock_get):
        index_response = MagicMock()
        index_response.raise_for_status = MagicMock()
        index_response.json.return_value = {
            "data": [{"type": "oracle_cards", "jsonl_download_uri": "https://example.com/oracle.jsonl.gz"}]
        }
        bulk_response = MagicMock()
        bulk_response.raise_for_status = MagicMock()
        bulk_response.content = self._jsonl_gzip(
            [
                {
                    "name": "Sol Ring",
                    "id": "11111111-1111-1111-1111-111111111111",
                    "mana_cost": "{1}",
                    "cmc": 1,
                    "type_line": "Artifact",
                    "oracle_text": "{T}: Add {C}{C}.",
                    "color_identity": [],
                    "layout": "normal",
                }
            ]
        )
        mock_get.side_effect = [index_response, bulk_response]

        count = sync_scryfall_cards()

        self.assertEqual(count, 1)
        card = Card.objects.get(name="Sol Ring")
        self.assertEqual(str(card.scryfall_id), "11111111-1111-1111-1111-111111111111")
        self.assertEqual(card.roles, ["ramp"])

    @patch("cards.services.requests.get")
    def test_double_faced_card_joins_faces_with_double_slash(self, mock_get):
        index_response = MagicMock()
        index_response.raise_for_status = MagicMock()
        index_response.json.return_value = {
            "data": [{"type": "oracle_cards", "jsonl_download_uri": "https://example.com/oracle.jsonl.gz"}]
        }
        bulk_response = MagicMock()
        bulk_response.raise_for_status = MagicMock()
        bulk_response.content = self._jsonl_gzip(
            [
                {
                    "name": "Fire // Ice",
                    "id": "22222222-2222-2222-2222-222222222222",
                    "layout": "split",
                    "card_faces": [
                        {"oracle_text": "Deals 2 damage.", "type_line": "Instant"},
                        {"oracle_text": "Tap target permanent.", "type_line": "Instant"},
                    ],
                }
            ]
        )
        mock_get.side_effect = [index_response, bulk_response]

        sync_scryfall_cards()

        card = Card.objects.get(name="Fire // Ice")
        self.assertEqual(card.oracle_text, "Deals 2 damage. // Tap target permanent.")

    @patch("cards.services.requests.get")
    def test_non_card_layouts_are_skipped(self, mock_get):
        index_response = MagicMock()
        index_response.raise_for_status = MagicMock()
        index_response.json.return_value = {
            "data": [{"type": "oracle_cards", "jsonl_download_uri": "https://example.com/oracle.jsonl.gz"}]
        }
        bulk_response = MagicMock()
        bulk_response.raise_for_status = MagicMock()
        bulk_response.content = self._jsonl_gzip(
            [{"name": "Soldier", "id": "33333333-3333-3333-3333-333333333333", "layout": "token"}]
        )
        mock_get.side_effect = [index_response, bulk_response]

        count = sync_scryfall_cards()

        self.assertEqual(count, 0)
        self.assertFalse(Card.objects.filter(name="Soldier").exists())

    @patch("cards.services.requests.get")
    def test_full_replace_removes_old_cards(self, mock_get):
        Card.objects.create(name="Old Card")
        index_response = MagicMock()
        index_response.raise_for_status = MagicMock()
        index_response.json.return_value = {
            "data": [{"type": "oracle_cards", "jsonl_download_uri": "https://example.com/oracle.jsonl.gz"}]
        }
        bulk_response = MagicMock()
        bulk_response.raise_for_status = MagicMock()
        bulk_response.content = self._jsonl_gzip(
            [{"name": "New Card", "id": "44444444-4444-4444-4444-444444444444", "layout": "normal"}]
        )
        mock_get.side_effect = [index_response, bulk_response]

        sync_scryfall_cards()

        self.assertFalse(Card.objects.filter(name="Old Card").exists())
        self.assertTrue(Card.objects.filter(name="New Card").exists())

    @patch("cards.services.requests.get")
    def test_duplicate_names_first_occurrence_wins(self, mock_get):
        index_response = MagicMock()
        index_response.raise_for_status = MagicMock()
        index_response.json.return_value = {
            "data": [{"type": "oracle_cards", "jsonl_download_uri": "https://example.com/oracle.jsonl.gz"}]
        }
        bulk_response = MagicMock()
        bulk_response.raise_for_status = MagicMock()
        bulk_response.content = self._jsonl_gzip(
            [
                {"name": "Dupe", "id": "55555555-5555-5555-5555-555555555555", "layout": "normal"},
                {"name": "Dupe", "id": "66666666-6666-6666-6666-666666666666", "layout": "normal"},
            ]
        )
        mock_get.side_effect = [index_response, bulk_response]

        sync_scryfall_cards()

        card = Card.objects.get(name="Dupe")
        self.assertEqual(str(card.scryfall_id), "55555555-5555-5555-5555-555555555555")
