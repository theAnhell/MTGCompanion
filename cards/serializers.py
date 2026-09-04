from rest_framework import serializers

from .models import Card


class SyncStatusSerializer(serializers.Serializer):
    cardCount = serializers.IntegerField(source="card_count")
    syncedAt = serializers.DateTimeField(source="synced_at", allow_null=True)


class CardSummarySerializer(serializers.ModelSerializer):
    manaCost = serializers.CharField(source="mana_cost", allow_null=True)
    typeLine = serializers.CharField(source="type_line", allow_null=True)
    colorIdentity = serializers.ListField(source="color_identity", allow_null=True)

    class Meta:
        model = Card
        fields = ["name", "manaCost", "typeLine", "colorIdentity"]
