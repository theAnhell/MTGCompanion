from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Player
from .serializers import PlayerSerializer
from .services import find_player_by_identifier


class PlayerListView(ListAPIView):
    serializer_class = PlayerSerializer

    def get_queryset(self):
        queryset = Player.objects.all().order_by("name")
        include_merged = self.request.query_params.get("includeMerged") == "true"
        if not include_merged:
            queryset = queryset.filter(merged_into__isnull=True)
        return queryset


class PlayerDetailView(RetrieveAPIView):
    serializer_class = PlayerSerializer

    def get_object(self):
        player = find_player_by_identifier(self.kwargs["id"])
        if player is None:
            raise NotFound(f"Player not found: {self.kwargs['id']}")
        return player
