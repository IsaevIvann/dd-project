from django.conf import settings
from .stations import STATIONS

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

def stations_nav(request):
    items = [(k, v["title"]) for k, v in STATIONS.items()]
    return {"STATIONS_NAV": items}