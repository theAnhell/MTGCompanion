from rest_framework import serializers


class RetiredDeckSerializer(serializers.Serializer):
    commanderId = serializers.UUIDField(source="commander_id")
    commanderName = serializers.CharField(source="commander.name")
    source = serializers.CharField()


class DeckCardSerializer(serializers.Serializer):
    cardName = serializers.CharField(source="card_name")
    setCode = serializers.CharField(source="set_code", allow_null=True)
    collectorNumber = serializers.CharField(source="collector_number", allow_null=True)
    quantity = serializers.IntegerField()
    isFoil = serializers.BooleanField(source="is_foil")
    isCommander = serializers.BooleanField(source="is_commander")


class DeckSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    ownerId = serializers.UUIDField(source="owner_id")
    ownerName = serializers.CharField(source="owner.name")
    commanderId = serializers.UUIDField(source="commander_id")
    commanderName = serializers.CharField(source="commander.name")
    name = serializers.CharField(allow_null=True)
    source = serializers.CharField()
    moxfieldDeckId = serializers.CharField(source="moxfield_deck_id", allow_null=True)
    moxfieldUrl = serializers.CharField(source="moxfield_url", allow_null=True)
    cardCount = serializers.SerializerMethodField()

    def get_cardCount(self, obj) -> int:
        # `cards` is prefetched by the view so this doesn't re-query per row.
        return len(obj.cards.all())


class DeckDetailSerializer(DeckSerializer):
    cards = DeckCardSerializer(many=True)
