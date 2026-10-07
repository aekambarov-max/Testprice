from django.urls import path

from .views import NsiProductSearchView

urlpatterns = [path("nsi/products/", NsiProductSearchView.as_view())]
