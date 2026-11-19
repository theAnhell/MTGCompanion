import uuid

from rest_framework.test import APITestCase

from binder.models import BinderCard
from cards.models import Card
from players.models import Player


class BinderViewTests(APITestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Owner")

    def test_get_empty_binder(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}/binder")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_put_replaces_binder_and_full_replaces_on_second_call(self):
        self.client.put(
            f"/api/v1/players/{self.player.id}/binder",
            {"exportText": "1 Sol Ring (LEA) 226"},
            format="json",
        )
        response = self.client.put(
            f"/api/v1/players/{self.player.id}/binder",
            {"exportText": "1 Arcane Signet (MSC) 1"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        names = [c["cardName"] for c in response.data]
        self.assertEqual(names, ["Arcane Signet"])
        self.assertEqual(BinderCard.objects.filter(player=self.player).count(), 1)

    def test_put_missing_export_text_400s(self):
        response = self.client.put(f"/api/v1/players/{self.player.id}/binder", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_get_includes_scryfall_id_when_known(self):
        Card.objects.create(name="Sol Ring", scryfall_id="11111111-1111-1111-1111-111111111111")
        BinderCard.objects.create(id=uuid.uuid4(), player=self.player, card_name="Sol Ring", quantity=1)

        response = self.client.get(f"/api/v1/players/{self.player.id}/binder")

        self.assertEqual(response.data[0]["scryfallId"], "11111111-1111-1111-1111-111111111111")

    def test_get_scryfall_id_null_when_unknown(self):
        BinderCard.objects.create(id=uuid.uuid4(), player=self.player, card_name="Unknown Card", quantity=1)

        response = self.client.get(f"/api/v1/players/{self.player.id}/binder")

        self.assertIsNone(response.data[0]["scryfallId"])

    def test_binder_by_player_name(self):
        response = self.client.get("/api/v1/players/Owner/binder")
        self.assertEqual(response.status_code, 200)

    def test_unknown_player_404s(self):
        response = self.client.get(f"/api/v1/players/{uuid.uuid4()}/binder")
        self.assertEqual(response.status_code, 404)
