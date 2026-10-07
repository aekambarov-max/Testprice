from django.urls import path

from .views import KpResponseView, SupplierListView

urlpatterns = [
    path("suppliers/", SupplierListView.as_view()),
    path("kp-responses/<uuid:token>/", KpResponseView.as_view()),
]
