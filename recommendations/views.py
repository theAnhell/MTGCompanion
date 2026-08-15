from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from decks.models import Deck

from .models import Recommendation
from .serializers import RecommendationSerializer
from .services import generate_recommendations, list_recommendations, update_recommendation


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
