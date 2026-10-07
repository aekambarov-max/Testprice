from django.urls import path

from . import views

urlpatterns = [
    path("auth/me/", views.MeView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("dzos/", views.DzoListView.as_view()),
    path("users/search/", views.UserSearchView.as_view()),
    path("notifications/", views.NotificationListView.as_view()),
    path("notifications/read/", views.mark_notifications_read),
]
