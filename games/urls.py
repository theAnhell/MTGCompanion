from django.urls import path

from .views import GameDetailView, GameListView

urlpatterns = [
    path("games", GameListView.as_view()),
    path("games/<str:id>", GameDetailView.as_view()),
]
