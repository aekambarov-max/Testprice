from .models import Dzo, UserProfile
from .roles import is_admin


def marketer_dzo_ids(user):
    """ДЗО, по которым пользователь может вести маркетинговый анализ (своё ДЗО + выданные доступы)."""
    if is_admin(user):
        return set(Dzo.objects.filter(is_active=True).values_list("pk", flat=True))
    profile = UserProfile.objects.filter(user=user).prefetch_related("allowed_dzos").first()
    if profile is None:
        return set()
    ids = {d.pk for d in profile.allowed_dzos.all()}
    if profile.dzo_id:
        ids.add(profile.dzo_id)
    return ids
