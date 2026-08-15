from rest_framework import serializers

from .models import Game, GamePlayer


class GameSerializer(serializers.ModelSerializer):
    createdOn = serializers.SerializerMethodField()
    totalTurns = serializers.IntegerField(source="total_turns", allow_null=True)
    gameTimeInMinutes = serializers.IntegerField(source="game_time_in_minutes", allow_null=True)
    winCondition = serializers.IntegerField(source="win_condition", allow_null=True)
    isPublic = serializers.BooleanField(source="is_public")

    class Meta:
        model = Game
        fields = ["id", "name", "notes", "createdOn", "totalTurns", "gameTimeInMinutes", "winCondition", "isPublic"]

    def get_createdOn(self, obj) -> str:
        """Matches Node's `new Date(row.created_on).toISOString()` (millisecond
        precision, trailing Z) rather than DRF's default microsecond ISO format."""
        return obj.created_on.strftime("%Y-%m-%dT%H:%M:%S.") + f"{obj.created_on.microsecond // 1000:03d}Z"


class GamePlayerDetailSerializer(serializers.ModelSerializer):
    playerId = serializers.UUIDField(source="player_id")
    playerName = serializers.CharField(source="player.name")
    commanderId = serializers.UUIDField(source="commander_id")
    commanderName = serializers.CharField(source="commander.name")
    commanderPartnerId = serializers.UUIDField(source="commander_partner_id", allow_null=True)
    commanderPartnerName = serializers.SerializerMethodField()
    turnOrder = serializers.IntegerField(source="turn_order", allow_null=True)
    mulligans = serializers.IntegerField(allow_null=True)
    isWinner = serializers.BooleanField(source="is_winner")

    class Meta:
        model = GamePlayer
        fields = [
            "playerId",
            "playerName",
            "commanderId",
            "commanderName",
            "commanderPartnerId",
            "commanderPartnerName",
            "turnOrder",
            "mulligans",
            "isWinner",
        ]

    def get_commanderPartnerName(self, obj):
        return obj.commander_partner.name if obj.commander_partner_id else None
