from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ki_radar.accounts.permissions import is_business_owner, is_coordinator

SUPPORTED_USE_CASE_ROLES = {
    "business_owner",
    "coordinator",
    "technical_owner",
}


def _current_active_user(user):
    user_id = getattr(user, "pk", None)
    if user_id is None:
        return None
    return (
        get_user_model()
        .objects.filter(pk=user_id, is_active=True, is_anonymized=False)
        .first()
    )


def revalidate_use_case_role(*, role_key: str, user, required: bool = False):
    """Revalidate an explicit role selection against the current database state."""

    if role_key not in SUPPORTED_USE_CASE_ROLES:
        raise ValidationError("Unbekannte Use-Case-Rolle.")
    if user is None:
        if required:
            raise ValidationError("Für diese Rolle ist eine Person erforderlich.")
        return None

    current = _current_active_user(user)
    if current is None:
        raise ValidationError(
            "Die ausgewählte Person ist nicht mehr aktiv oder wurde anonymisiert."
        )

    if role_key == "business_owner" and not is_business_owner(current):
        raise ValidationError(
            "Die ausgewählte Person ist aktuell nicht als Business Owner zulässig."
        )
    if role_key == "coordinator" and not is_coordinator(current):
        raise ValidationError(
            "Die ausgewählte Person ist aktuell nicht als KI-Koordinator zulässig."
        )

    return current
