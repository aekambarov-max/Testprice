from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.nsi.urls")),
    path("api/", include("apps.suppliers.urls")),
    path("api/", include("apps.pricing.urls")),
    path("api/", include("apps.marketing_analysis.urls")),
]
