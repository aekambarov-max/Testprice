from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dzo, Notification
from .serializers import DzoSerializer, MeSerializer, NotificationSerializer, UserShortSerializer


def _me_payload(request):
    data = MeSerializer(request.user).data if request.user.is_authenticated else None
    return {"user": data, "features": {"marketing_analysis": settings.MA_ENABLED}}


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        get_token(request)
        return Response(_me_payload(request))


class LoginView(APIView):
    """Вход по локальной учётной записи. TODO(PO): LDAP/AD через django-auth-ldap (AUTHENTICATION_BACKENDS)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = authenticate(request, username=request.data.get("username"), password=request.data.get("password"))
        if user is None:
            return Response({"code": "invalid_credentials", "detail": "Неверный логин или пароль"}, status=400)
        login(request, user)
        return Response(_me_payload(request))


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DzoListView(generics.ListAPIView):
    serializer_class = DzoSerializer
    pagination_class = None
    queryset = Dzo.objects.filter(is_active=True)


class UserSearchView(generics.ListAPIView):
    """Поиск сотрудников по ФИО/логину (справочник пользователей, в проде синхронизирован с LDAP/AD)."""

    serializer_class = UserShortSerializer
    pagination_class = None

    def get_queryset(self):
        q = (self.request.query_params.get("q") or "").strip()
        qs = get_user_model().objects.filter(is_active=True).select_related("profile", "profile__dzo")
        if q:
            for term in q.split():
                qs = qs.filter(
                    Q(last_name__icontains=term)
                    | Q(first_name__icontains=term)
                    | Q(profile__middle_name__icontains=term)
                    | Q(username__icontains=term)
                )
        dzo = self.request.query_params.get("dzo")
        if dzo:
            qs = qs.filter(profile__dzo_id=dzo)
        return qs.order_by("last_name", "first_name")[:20]


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["unread"] = Notification.objects.filter(user=request.user, is_read=False).count()
        return response


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_read(request):
    ids = request.data.get("ids")
    qs = Notification.objects.filter(user=request.user, is_read=False)
    if ids:
        qs = qs.filter(pk__in=ids)
    qs.update(is_read=True)
    return Response(status=status.HTTP_204_NO_CONTENT)
