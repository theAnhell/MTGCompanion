from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", lambda request: JsonResponse({"status": "ok"})),
    path("api/v1/", include("players.urls")),
    path("api/v1/", include("commanders.urls")),
    path("api/v1/", include("games.urls")),
    path("api/v1/", include("decks.urls")),
    path("api/v1/", include("binder.urls")),
    path("api/v1/", include("cards.urls")),
    path("api/v1/", include("recommendations.urls")),
    path("api/v1/", include("stats.urls")),
]


def handler404(request, exception=None):
    return JsonResponse({"error": f"Not found: {request.method} {request.path}"}, status=404)
