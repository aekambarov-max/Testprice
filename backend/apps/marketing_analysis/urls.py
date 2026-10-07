from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import MarketingAnalysisViewSet

router = SimpleRouter()
router.register("marketing-analyses", MarketingAnalysisViewSet, basename="marketing-analysis")

urlpatterns = [
    # Ссылка на файл без завершающего слэша: /api/marketing-analyses/{id}/conclusion.pdf
    path("marketing-analyses/<int:pk>/conclusion.pdf", MarketingAnalysisViewSet.as_view({"get": "conclusion"}),
         name="marketing-analysis-conclusion-file"),
    *router.urls,
]
