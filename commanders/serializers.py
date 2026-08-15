from rest_framework import serializers

from .models import Commander


class CommanderSerializer(serializers.ModelSerializer):
    imageUri = serializers.CharField(source="image_uri", allow_null=True)
    edhrecRank = serializers.IntegerField(source="edhrec_rank", allow_null=True)
    cmc = serializers.DecimalField(max_digits=4, decimal_places=1, allow_null=True, coerce_to_string=False)
    deckName = serializers.CharField(source="deck_name", allow_null=True)
    decklistUrl = serializers.CharField(source="decklist_url", allow_null=True)

    class Meta:
        model = Commander
        fields = ["id", "name", "colors", "imageUri", "edhrecRank", "cmc", "deckName", "decklistUrl"]
