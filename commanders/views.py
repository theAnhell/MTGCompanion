from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Commander
from .serializers import CommanderSerializer


class CommanderListView(ListAPIView):
    serializer_class = CommanderSerializer

    def get_queryset(self):
        queryset = Commander.objects.all().order_by("name")
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class CommanderDetailView(RetrieveAPIView):
    queryset = Commander.objects.all()
    serializer_class = CommanderSerializer
    lookup_field = "id"
