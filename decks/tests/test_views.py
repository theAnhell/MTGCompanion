import uuid

from rest_framework.test import APITestCase

from commanders.models import Commander
from decks.models import Deck, DeckCard
from players.models import Player


class DeckListCreateViewTests(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")

    def test_list_requires_player_id(self):
        response = self.client.get("/api/v1/decks")
        self.assertEqual(response.status_code, 400)

    def test_list_returns_owners_decks(self):
        Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        response = self.client.get(f"/api/v1/decks?playerId={self.owner.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_deck_parses_export_and_flags_commander(self):
        body = {
            "ownerId": str(self.owner.id),
            "commanderId": str(self.commander.id),
            "exportText": "1 Queen Marchesa (SLD) 1\n1 Sol Ring (LEA) 226",
        }
        response = self.client.post("/api/v1/decks", body, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cardCount"], 2)
        cards = {c["cardName"]: c for c in response.data["cards"]}
        self.assertTrue(cards["Queen Marchesa"]["isCommander"])
        self.assertFalse(cards["Sol Ring"]["isCommander"])

    def test_create_deck_missing_fields_400s(self):
        response = self.client.post("/api/v1/decks", {"ownerId": str(self.owner.id)}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_deck_unknown_commander_404s(self):
        body = {
            "ownerId": str(self.owner.id),
            "commanderId": str(uuid.uuid4()),
            "exportText": "1 Sol Ring (LEA) 226",
        }
        response = self.client.post("/api/v1/decks", body, format="json")
        self.assertEqual(response.status_code, 404)


class DeckDetailViewTests(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        DeckCard.objects.create(deck=self.deck, card_name="Sol Ring", quantity=1)

    def test_get_deck_includes_cards(self):
        response = self.client.get(f"/api/v1/decks/{self.deck.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["cards"]), 1)

    def test_get_missing_deck_404s(self):
        response = self.client.get(f"/api/v1/decks/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_delete_deck(self):
        response = self.client.delete(f"/api/v1/decks/{self.deck.id}")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Deck.objects.filter(pk=self.deck.id).exists())

    def test_delete_missing_deck_404s(self):
        response = self.client.delete(f"/api/v1/decks/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)


class DeckCardsViewTests(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        DeckCard.objects.create(deck=self.deck, card_name="Sol Ring", quantity=1)

    def test_put_replaces_decklist(self):
        response = self.client.put(
            f"/api/v1/decks/{self.deck.id}/cards",
            {"exportText": "1 Arcane Signet (MSC) 1"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        names = [c["cardName"] for c in response.data["cards"]]
        self.assertEqual(names, ["Arcane Signet"])

    def test_put_missing_export_text_400s(self):
        response = self.client.put(f"/api/v1/decks/{self.deck.id}/cards", {}, format="json")
        self.assertEqual(response.status_code, 400)


class DeckArchetypeStatsViewTests(APITestCase):
    def test_returns_targets_from_settings(self):
        owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        deck = Deck.objects.create(id=uuid.uuid4(), owner=owner, commander=commander)

        response = self.client.get(f"/api/v1/decks/{deck.id}/archetype-stats")

        self.assertEqual(response.status_code, 200)
        for role in ["ramp", "draw", "removal", "land"]:
            self.assertIn(role, response.data)
            self.assertEqual(response.data[role]["count"], 0)
            self.assertFalse(response.data[role]["met"])

    def test_missing_deck_404s(self):
        response = self.client.get(f"/api/v1/decks/{uuid.uuid4()}/archetype-stats")
        self.assertEqual(response.status_code, 404)


class RetiredDecksViewTests(APITestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")

    def test_post_adds_retired_deck(self):
        response = self.client.post(
            f"/api/v1/players/{self.player.id}/retired-decks",
            {"commanderId": str(self.commander.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        listing = self.client.get(f"/api/v1/players/{self.player.id}/retired-decks")
        self.assertEqual(len(listing.data), 1)

    def test_post_unknown_commander_404s(self):
        response = self.client.post(
            f"/api/v1/players/{self.player.id}/retired-decks",
            {"commanderId": str(uuid.uuid4())},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_retired_deck(self):
        self.client.post(
            f"/api/v1/players/{self.player.id}/retired-decks",
            {"commanderId": str(self.commander.id)},
            format="json",
        )
        response = self.client.delete(
            f"/api/v1/players/{self.player.id}/retired-decks/{self.commander.id}"
        )
        self.assertEqual(response.status_code, 204)

        listing = self.client.get(f"/api/v1/players/{self.player.id}/retired-decks")
        self.assertEqual(len(listing.data), 0)

    def test_retired_decks_by_player_name(self):
        response = self.client.get("/api/v1/players/Owner/retired-decks")
        self.assertEqual(response.status_code, 200)
