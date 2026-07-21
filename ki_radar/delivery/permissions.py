from ki_radar.accounts.permissions import is_coordinator
from ki_radar.use_cases.permissions import can_view_use_case

from .models import DeliveryPackage


def can_view_package(user, package: DeliveryPackage) -> bool:
    return can_view_use_case(user, package.use_case)


def can_create_package(user) -> bool:
    return is_coordinator(user)


def can_edit_package(user, package: DeliveryPackage) -> bool:
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        return False
    return is_coordinator(user) or package.use_case.business_owner_id == user.id


def can_transition_package(user) -> bool:
    return is_coordinator(user)
