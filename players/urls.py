from django.urls import path

from .views import PlayerDetailView, PlayerListView

urlpatterns = [
    path("players", PlayerListView.as_view()),
    path("players/<str:id>", PlayerDetailView.as_view()),
]
