from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """Reshapes DRF's default error body ({"detail": ...} for NotFound, a bare
    list for a ValidationError(str)) into {"error": ...}, matching the Node
    app's HttpError middleware (src/app.ts)."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error": str(response.data["detail"])}
    elif isinstance(response.data, list) and response.data:
        response.data = {"error": str(response.data[0])}
    return response
