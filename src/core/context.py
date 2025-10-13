from django.conf import settings

def site_globals(request):
    # Чистый путь без querystring
    path = request.path or "/"

    # Гарантируем конечный слэш (Яндекс это любит)
    if not path.endswith("/"):
        path = f"{path}/"

    return {
        "SITE_URL": getattr(settings, "SITE_URL", "").rstrip("/"),
        "CANONICAL_PATH": path,
    }