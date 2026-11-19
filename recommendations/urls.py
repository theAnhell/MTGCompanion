from django.urls import path

from .views import (
    DeckRecommendationsGenerateView,
    DeckRecommendationsView,
    PlayerBinderFitView,
    PlayerCardFitView,
    RecommendationDetailView,
)

urlpatterns = [
    path("decks/<str:id>/recommendations", DeckRecommendationsView.as_view()),
    path("decks/<str:id>/recommendations/generate", DeckRecommendationsGenerateView.as_view()),
    path("recommendations/<str:id>", RecommendationDetailView.as_view()),
    path("players/<str:id>/card-fit", PlayerCardFitView.as_view()),
    path("players/<str:id>/binder-fits", PlayerBinderFitView.as_view()),
]
