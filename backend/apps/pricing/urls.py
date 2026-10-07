from django.urls import path

from .views import PriceCatalogListView

urlpatterns = [path("price-catalog/", PriceCatalogListView.as_view())]
