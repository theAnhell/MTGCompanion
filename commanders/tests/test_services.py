import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from commanders.models import Commander, CommanderCardStat
from commanders.services import (
    _extract_current_rank,
    _flatten_card_stats,
    get_edhrec_url,
    is_stale,
    slugify_commander_name,
    sync_commander_card_stats,
)


class SlugifyCommanderNameTests(SimpleTestCase):
    def test_plain_name(self):
        self.assertEqual(slugify_commander_name("Queen Marchesa"), "queen-marchesa")

    def test_apostrophe_dropped_not_hyphenated(self):
        self.assertEqual(
            slugify_commander_name("Saheeli, the Sun's Brilliance"), "saheeli-the-suns-brilliance"
        )

    def test_accented_characters_transliterated(self):
        self.assertEqual(slugify_commander_name("Éowyn, Shieldmaiden"), "eowyn-shieldmaiden")

    def test_partner_pair_concatenates_both_slugs(self):
        self.assertEqual(
            slugify_commander_name("Silas Renn, Seeker Adept || Tana, the Bloodsower (Partners)"),
            "silas-renn-seeker-adept-tana-the-bloodsower",
        )

    def test_mdfc_uses_front_face_only(self):
        self.assertEqual(
            slugify_commander_name("Valentin, Dean of the Vein // Lisette, Dean of the Root"),
            "valentin-dean-of-the-vein",
        )

    def test_other_punctuation_hyphenated(self):
        self.assertEqual(slugify_commander_name("Henzie \"Toolbox\" Torre"), "henzie-toolbox-torre")


class IsStaleTests(TestCase):
    def test_never_synced_is_stale(self):
        commander = Commander.objects.create(id=uuid.uuid4(), name="Fresh Commander", edhrec_synced_at=None)
        self.assertTrue(is_stale(commander))

    def test_recently_synced_not_stale(self):
        commander = Commander.objects.create(
            id=uuid.uuid4(), name="Recent Commander", edhrec_synced_at=timezone.now()
        )
        self.assertFalse(is_stale(commander))

    def test_old_sync_is_stale(self):
        commander = Commander.objects.create(
            id=uuid.uuid4(),
            name="Old Commander",
            edhrec_synced_at=timezone.now() - timedelta(days=15),
        )
        self.assertTrue(is_stale(commander))


class GetEdhrecUrlTests(TestCase):
    def test_uses_derived_slug_by_default(self):
        commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.assertEqual(get_edhrec_url(commander), "https://edhrec.com/commanders/queen-marchesa")

    def test_manual_slug_override_wins(self):
        commander = Commander.objects.create(
            id=uuid.uuid4(), name="Some Weird Name", edhrec_slug="custom-slug"
        )
        self.assertEqual(get_edhrec_url(commander), "https://edhrec.com/commanders/custom-slug")


class FlattenCardStatsTests(SimpleTestCase):
    def test_flattens_type_category_cardlists(self):
        payload = {
            "container": {
                "json_dict": {
                    "cardlists": [
                        {
                            "tag": "creatures",
                            "header": "Creatures",
                            "cardviews": [
                                {"name": "Card A", "num_decks": 50, "potential_decks": 100, "synergy": 0.2},
                            ],
                        }
                    ]
                }
            }
        }
        rows = _flatten_card_stats(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["card_name"], "Card A")
        self.assertEqual(rows[0]["inclusion_rate"], 50.0)

    def test_excludes_cross_cutting_tags(self):
        payload = {
            "container": {
                "json_dict": {
                    "cardlists": [
                        {
                            "tag": "highsynergycards",
                            "header": "High Synergy Cards",
                            "cardviews": [{"name": "Card B", "num_decks": 10, "potential_decks": 100}],
                        }
                    ]
                }
            }
        }
        self.assertEqual(_flatten_card_stats(payload), [])

    def test_skips_entries_with_no_potential_decks(self):
        payload = {
            "container": {
                "json_dict": {
                    "cardlists": [
                        {
                            "tag": "lands",
                            "header": "Lands",
                            "cardviews": [{"name": "Card C", "num_decks": 0, "potential_decks": 0}],
                        }
                    ]
                }
            }
        }
        self.assertEqual(_flatten_card_stats(payload), [])


class ExtractCurrentRankTests(SimpleTestCase):
    def test_uses_latest_month(self):
        payload = {
            "panels": {
                "rank_over_time": {
                    "2026-06-01": {"rank": 500},
                    "2026-08-01": {"rank": 100},
                    "2026-07-01": {"rank": 300},
                }
            }
        }
        self.assertEqual(_extract_current_rank(payload), 100)

    def test_missing_panel_returns_none(self):
        self.assertIsNone(_extract_current_rank({"panels": {}}))

    def test_missing_panels_key_returns_none(self):
        self.assertIsNone(_extract_current_rank({}))


class SyncCommanderCardStatsTests(TestCase):
    def setUp(self):
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")

    def _mock_response(self, payload):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = payload
        return response

    @patch("commanders.services.requests.get")
    def test_full_replaces_stats_and_updates_rank(self, mock_get):
        payload = {
            "container": {
                "json_dict": {
                    "cardlists": [
                        {
                            "tag": "creatures",
                            "header": "Creatures",
                            "cardviews": [{"name": "Card A", "num_decks": 40, "potential_decks": 80}],
                        }
                    ]
                }
            },
            "panels": {"rank_over_time": {"2026-07-01": {"rank": 77}}},
        }
        mock_get.return_value = self._mock_response(payload)

        count = sync_commander_card_stats(self.commander.id)

        self.assertEqual(count, 1)
        self.commander.refresh_from_db()
        self.assertEqual(self.commander.edhrec_rank, 77)
        self.assertIsNotNone(self.commander.edhrec_synced_at)
        self.assertEqual(CommanderCardStat.objects.filter(commander=self.commander).count(), 1)

    @patch("commanders.services.requests.get")
    def test_second_sync_fully_replaces_old_rows(self, mock_get):
        CommanderCardStat.objects.create(
            commander=self.commander,
            card_name="Stale Card",
            category="Creatures",
            num_decks=1,
            potential_decks=1,
            inclusion_rate=100.0,
        )
        payload = {
            "container": {"json_dict": {"cardlists": []}},
            "panels": {},
        }
        mock_get.return_value = self._mock_response(payload)

        sync_commander_card_stats(self.commander.id)

        self.assertEqual(CommanderCardStat.objects.filter(commander=self.commander).count(), 0)

    @patch("commanders.services.requests.get")
    def test_uses_manual_slug_override_for_fetch_url(self, mock_get):
        self.commander.edhrec_slug = "custom-slug"
        self.commander.save(update_fields=["edhrec_slug"])
        mock_get.return_value = self._mock_response(
            {"container": {"json_dict": {"cardlists": []}}, "panels": {}}
        )

        sync_commander_card_stats(self.commander.id)

        called_url = mock_get.call_args[0][0]
        self.assertIn("custom-slug", called_url)
