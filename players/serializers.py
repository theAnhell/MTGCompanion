from rest_framework import serializers

from .models import Player


class PlayerSerializer(serializers.ModelSerializer):
    isYou = serializers.BooleanField(source="is_you")
    isRandom = serializers.BooleanField(source="is_random")
    mergedIntoId = serializers.UUIDField(source="merged_into_id", allow_null=True)

    class Meta:
        model = Player
        fields = ["id", "name", "username", "color", "isYou", "isRandom", "favorite", "mergedIntoId"]
