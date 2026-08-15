from django.urls import path

from .views import RetiredDeckDetailView, RetiredDecksView

urlpatterns = [
    path("players/<str:id>/retired-decks", RetiredDecksView.as_view()),
    path("players/<str:id>/retired-decks/<str:commander_id>", RetiredDeckDetailView.as_view()),
]
