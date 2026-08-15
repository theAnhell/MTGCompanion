from rest_framework import serializers


class RecommendationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    deckId = serializers.UUIDField(source="deck_id")
    action = serializers.CharField()
    cardName = serializers.CharField(source="card_name")
    inclusionRate = serializers.DecimalField(
        source="inclusion_rate", max_digits=5, decimal_places=1, coerce_to_string=False
    )
    role = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    appliedAt = serializers.DateTimeField(source="applied_at", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at")
