from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    data = {
        "status": "ok",
        "debug": settings.DEBUG,
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "database_engine": settings.DATABASES["default"]["ENGINE"],
        "render_hostname": getattr(settings, "RENDER_EXTERNAL_HOSTNAME", None),
        "static_storage": settings.STATICFILES_STORAGE,
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        data["database"] = "connected"
    except Exception as exc:
        data["status"] = "error"
        data["database"] = "failed"
        data["database_error"] = str(exc)
        return JsonResponse(data, status=500)

    try:
        from store.models import Watch

        data["watch_count"] = Watch.objects.count()
    except Exception as exc:
        data["status"] = "error"
        data["watch_count_error"] = str(exc)
        return JsonResponse(data, status=500)

    return JsonResponse(data)
