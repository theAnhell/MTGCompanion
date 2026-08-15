from rest_framework import serializers

from commanders.services import get_edhrec_url


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
    edhrecUrl = serializers.SerializerMethodField()
    cardCount = serializers.SerializerMethodField()

    def get_cardCount(self, obj) -> int:
        # Sum quantity, not row count — Moxfield collapses repeated basics
        # (e.g. "3 Plains") into a single row with quantity=3.
        # `cards` is prefetched by the view so this doesn't re-query per row.
        return sum(c.quantity for c in obj.cards.all())

    def get_edhrecUrl(self, obj) -> str:
        return get_edhrec_url(obj.commander)


class DeckDetailSerializer(DeckSerializer):
    cards = DeckCardSerializer(many=True)
