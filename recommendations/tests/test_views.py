import uuid

from django.utils import timezone
from rest_framework.test import APITestCase

from binder.models import BinderCard
from cards.models import Card
from commanders.models import Commander, CommanderCardStat
from decks.models import Deck, DeckCard
from players.models import Player
from recommendations.models import Recommendation


def _fresh_commander(name="Commander") -> Commander:
    return Commander.objects.create(id=uuid.uuid4(), name=name, edhrec_synced_at=timezone.now())


class DeckRecommendationsViewTests(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)

    def test_get_missing_deck_404s(self):
        response = self.client.get(f"/api/v1/decks/{uuid.uuid4()}/recommendations")
        self.assertEqual(response.status_code, 404)

    def test_get_empty_list(self):
        response = self.client.get(f"/api/v1/decks/{self.deck.id}/recommendations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_generate_creates_recommendations(self):
        BinderCard.objects.create(id=uuid.uuid4(), player=self.owner, card_name="Sol Ring", quantity=1)
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Sol Ring", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=90.0,
        )

        response = self.client.post(f"/api/v1/decks/{self.deck.id}/recommendations/generate")

        self.assertEqual(response.status_code, 201)
        cards = {r["cardName"] for r in response.data}
        self.assertIn("Sol Ring", cards)

    def test_generate_missing_deck_404s(self):
        response = self.client.post(f"/api/v1/decks/{uuid.uuid4()}/recommendations/generate")
        self.assertEqual(response.status_code, 404)


class RecommendationDetailViewTests(APITestCase):
    def setUp(self):
        owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        commander = _fresh_commander()
        deck = Deck.objects.create(id=uuid.uuid4(), owner=owner, commander=commander)
        self.rec = Recommendation.objects.create(
            player=owner, deck=deck, action=Recommendation.Action.ADD,
            card_name="Sol Ring", inclusion_rate=50.0,
        )

    def test_patch_status(self):
        response = self.client.patch(
            f"/api/v1/recommendations/{self.rec.id}", {"status": "approved"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "approved")

    def test_patch_invalid_status_400s(self):
        response = self.client.patch(
            f"/api/v1/recommendations/{self.rec.id}", {"status": "not-a-status"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_applied_non_bool_400s(self):
        response = self.client.patch(
            f"/api/v1/recommendations/{self.rec.id}", {"applied": "yes"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_missing_recommendation_404s(self):
        response = self.client.patch(
            f"/api/v1/recommendations/{uuid.uuid4()}", {"status": "approved"}, format="json"
        )
        self.assertEqual(response.status_code, 404)


class PlayerCardFitViewTests(APITestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = _fresh_commander()
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        Card.objects.create(name="Sol Ring")
        CommanderCardStat.objects.create(
            commander=self.commander, card_name="Sol Ring", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=80.0,
        )

    def test_requires_card_name(self):
        response = self.client.get(f"/api/v1/players/{self.owner.id}/card-fit")
        self.assertEqual(response.status_code, 400)

    def test_unknown_card_404s(self):
        response = self.client.get(
            f"/api/v1/players/{self.owner.id}/card-fit?cardName=Not A Real Card"
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_player_404s(self):
        response = self.client.get(f"/api/v1/players/{uuid.uuid4()}/card-fit?cardName=Sol Ring")
        self.assertEqual(response.status_code, 404)

    def test_returns_ranked_decks(self):
        response = self.client.get(f"/api/v1/players/{self.owner.id}/card-fit?cardName=Sol Ring")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["deckId"], str(self.deck.id))

    def test_works_by_player_name_too(self):
        response = self.client.get("/api/v1/players/Owner/card-fit?cardName=Sol Ring")
        self.assertEqual(response.status_code, 200)

    def test_invalid_limit_400s(self):
        response = self.client.get(
            f"/api/v1/players/{self.owner.id}/card-fit?cardName=Sol Ring&limit=notanumber"
        )
        self.assertEqual(response.status_code, 400)


class PlayerBinderFitViewTests(APITestCase):
    def test_unknown_player_404s(self):
        response = self.client.get(f"/api/v1/players/{uuid.uuid4()}/binder-fits")
        self.assertEqual(response.status_code, 404)

    def test_returns_fits(self):
        owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        commander = _fresh_commander()
        Deck.objects.create(id=uuid.uuid4(), owner=owner, commander=commander)
        BinderCard.objects.create(id=uuid.uuid4(), player=owner, card_name="Sol Ring", quantity=1)
        CommanderCardStat.objects.create(
            commander=commander, card_name="Sol Ring", category="c", num_decks=1,
            potential_decks=1, inclusion_rate=80.0,
        )

        response = self.client.get(f"/api/v1/players/{owner.id}/binder-fits")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["cardName"], "Sol Ring")
