from django.urls import path

from .views import (
    DeckArchetypeStatsView,
    DeckCardsView,
    DeckDetailView,
    DeckListCreateView,
    RetiredDeckDetailView,
    RetiredDecksView,
)

urlpatterns = [
    path("players/<str:id>/retired-decks", RetiredDecksView.as_view()),
    path("players/<str:id>/retired-decks/<str:commander_id>", RetiredDeckDetailView.as_view()),
    path("decks", DeckListCreateView.as_view()),
    path("decks/<str:id>", DeckDetailView.as_view()),
    path("decks/<str:id>/cards", DeckCardsView.as_view()),
    path("decks/<str:id>/archetype-stats", DeckArchetypeStatsView.as_view()),
]
