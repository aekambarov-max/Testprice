from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Dzo, Notification, full_name
from .roles import user_roles


class DzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dzo
        fields = ["id", "code", "name_ru", "name_kk"]


class UserShortSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    dzo = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name", "position", "department", "dzo"]

    def _profile(self, obj):
        return getattr(obj, "profile", None)

    def get_full_name(self, obj):
        return full_name(obj)

    def get_position(self, obj):
        p = self._profile(obj)
        return p.position if p else ""

    def get_department(self, obj):
        p = self._profile(obj)
        return p.department if p else ""

    def get_dzo(self, obj):
        p = self._profile(obj)
        return DzoSerializer(p.dzo).data if p and p.dzo else None


class MeSerializer(UserShortSerializer):
    roles = serializers.SerializerMethodField()
    allowed_dzos = serializers.SerializerMethodField()

    class Meta(UserShortSerializer.Meta):
        fields = UserShortSerializer.Meta.fields + ["email", "roles", "allowed_dzos"]

    def get_roles(self, obj):
        return sorted(user_roles(obj))

    def get_allowed_dzos(self, obj):
        from .access import marketer_dzo_ids

        return DzoSerializer(Dzo.objects.filter(pk__in=marketer_dzo_ids(obj)), many=True).data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "event", "title", "body", "link", "is_read", "created_at"]
