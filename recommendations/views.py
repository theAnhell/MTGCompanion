from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from cards.models import Card
from decks.models import Deck
from players.models import Player

from .models import Recommendation
from .serializers import BinderCardFitSerializer, CardFitSerializer, RecommendationSerializer
from .services import (
    find_best_decks_for_card,
    find_binder_card_fits,
    generate_recommendations,
    list_recommendations,
    update_recommendation,
)


def _require_deck(deck_id):
    if not Deck.objects.filter(pk=deck_id).exists():
        raise NotFound(f"Deck not found: {deck_id}")


class DeckRecommendationsView(APIView):
    def get(self, request, id):
        _require_deck(id)
        return Response(RecommendationSerializer(list_recommendations(id), many=True).data)


class DeckRecommendationsGenerateView(APIView):
    def post(self, request, id):
        _require_deck(id)
        recs = generate_recommendations(id)
        return Response(RecommendationSerializer(recs, many=True).data, status=HTTP_201_CREATED)


class RecommendationDetailView(APIView):
    def patch(self, request, id):
        if not Recommendation.objects.filter(pk=id).exists():
            raise NotFound(f"Recommendation not found: {id}")

        status_value = request.data.get("status")
        if status_value is not None:
            valid_statuses = {choice[0] for choice in Recommendation.Status.choices}
            if status_value not in valid_statuses:
                raise ValidationError(f"status must be one of {sorted(valid_statuses)}")

        applied = request.data.get("applied")
        if applied is not None and not isinstance(applied, bool):
            raise ValidationError("applied must be a boolean")

        rec = update_recommendation(id, status=status_value, applied=applied)
        return Response(RecommendationSerializer(rec).data)


class PlayerCardFitView(APIView):
    def get(self, request, id):
        if not Player.objects.filter(pk=id).exists():
            raise NotFound(f"Player not found: {id}")

        card_name = request.query_params.get("cardName")
        if not card_name:
            raise ValidationError("cardName is required")
        if not Card.objects.filter(pk=card_name).exists():
            raise NotFound(f"Card not found: {card_name}")

        limit = request.query_params.get("limit", 5)
        try:
            limit = int(limit)
        except ValueError:
            raise ValidationError("limit must be an integer")

        results = find_best_decks_for_card(id, card_name, limit=limit)
        return Response(CardFitSerializer(results, many=True).data)


class PlayerBinderFitView(APIView):
    def get(self, request, id):
        if not Player.objects.filter(pk=id).exists():
            raise NotFound(f"Player not found: {id}")

        results = find_binder_card_fits(id)
        return Response(BinderCardFitSerializer(results, many=True).data)
