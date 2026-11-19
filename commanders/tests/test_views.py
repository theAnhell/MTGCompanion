import uuid
from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase

from commanders.models import Commander
from decks.models import Deck
from players.models import Player


class CommanderListViewTests(APITestCase):
    def setUp(self):
        self.marchesa = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.ur_dragon = Commander.objects.create(id=uuid.uuid4(), name="The Ur-Dragon")

    def test_list_all(self):
        response = self.client.get("/api/v1/commanders")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_search_filters_case_insensitively(self):
        response = self.client.get("/api/v1/commanders?search=marchesa")
        self.assertEqual(response.status_code, 200)
        names = [c["name"] for c in response.data]
        self.assertEqual(names, ["Queen Marchesa"])

    def test_response_includes_edhrec_url(self):
        response = self.client.get("/api/v1/commanders?search=marchesa")
        self.assertEqual(response.data[0]["edhrecUrl"], "https://edhrec.com/commanders/queen-marchesa")


class CommanderDetailViewTests(APITestCase):
    def test_get_existing(self):
        commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        response = self.client.get(f"/api/v1/commanders/{commander.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Queen Marchesa")

    def test_get_missing_404s(self):
        response = self.client.get(f"/api/v1/commanders/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)


class CommanderEdhrecSyncTests(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.with_deck = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.without_deck = Commander.objects.create(id=uuid.uuid4(), name="The Ur-Dragon")
        Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.with_deck)

    def test_status_only_counts_commanders_with_decks(self):
        response = self.client.get("/api/v1/commanders/edhrec-sync-status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["commanderCount"], 1)
        self.assertEqual(response.data["staleCount"], 1)
        self.assertIsNone(response.data["oldestSyncedAt"])

    @patch("commanders.services.requests.get")
    def test_sync_only_touches_commanders_with_decks(self, mock_get):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"container": {"json_dict": {"cardlists": []}}, "panels": {}}
        mock_get.return_value = response

        result = self.client.post("/api/v1/commanders/edhrec-sync")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["commanderCount"], 1)
        self.assertEqual(result.data["staleCount"], 0)
        self.assertEqual(mock_get.call_count, 1)

        self.without_deck.refresh_from_db()
        self.assertIsNone(self.without_deck.edhrec_synced_at)

    @patch("commanders.services.requests.get")
    def test_sync_records_failures_without_aborting(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("boom")

        response = self.client.post("/api/v1/commanders/edhrec-sync")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["failedCommanderNames"], ["Queen Marchesa"])
