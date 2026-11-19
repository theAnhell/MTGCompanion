from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase

from cards.models import Card


class CardListViewTests(APITestCase):
    def setUp(self):
        Card.objects.create(name="Sol Ring", mana_cost="{1}", type_line="Artifact", color_identity=[])
        Card.objects.create(name="Mayhem Devil", type_line="Creature — Devil", color_identity=["B", "R"])

    def test_no_search_returns_empty(self):
        response = self.client.get("/api/v1/cards")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_search_matches_substring(self):
        response = self.client.get("/api/v1/cards?search=Sol")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c["name"] for c in response.data], ["Sol Ring"])

    def test_search_returns_color_identity(self):
        response = self.client.get("/api/v1/cards?search=Mayhem")
        self.assertEqual(response.data[0]["colorIdentity"], ["B", "R"])


class CardSyncStatusViewTests(APITestCase):
    def test_status_with_no_cards(self):
        response = self.client.get("/api/v1/cards/sync-status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cardCount"], 0)
        self.assertIsNone(response.data["syncedAt"])

    def test_status_with_cards(self):
        Card.objects.create(name="Sol Ring")
        response = self.client.get("/api/v1/cards/sync-status")
        self.assertEqual(response.data["cardCount"], 1)
        self.assertIsNotNone(response.data["syncedAt"])


class CardSyncViewTests(APITestCase):
    @patch("cards.views.sync_scryfall_cards")
    def test_sync_returns_status_after_sync(self, mock_sync):
        def fake_sync():
            Card.objects.create(name="Sol Ring")
            return 1

        mock_sync.side_effect = fake_sync

        response = self.client.post("/api/v1/cards/sync")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cardCount"], 1)
        mock_sync.assert_called_once()
