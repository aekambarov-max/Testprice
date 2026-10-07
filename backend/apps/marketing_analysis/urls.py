from rest_framework.routers import SimpleRouter

from .views import MarketingAnalysisViewSet

router = SimpleRouter()
router.register("marketing-analyses", MarketingAnalysisViewSet, basename="marketing-analysis")
urlpatterns = router.urls
