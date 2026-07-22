from ki_radar.accounts.permissions import (
    GROUP_BUSINESS_OWNER,
    GROUP_COORDINATOR,
    in_group,
    is_business_owner,
    is_coordinator,
)


def can_create_use_case(user) -> bool:
    return is_business_owner(user)


def can_edit_use_case(user, use_case) -> bool:
    return is_coordinator(user) or (
        is_business_owner(user) and use_case.business_owner_id == user.id
    )


def can_view_use_case(user, use_case) -> bool:
    return user.is_authenticated and not use_case.is_archived


def can_start_pilot(user, use_case) -> bool:
    """Allow the explicit Pilot start only to the accountable business roles."""

    if not user.is_authenticated:
        return False
    if in_group(user, GROUP_COORDINATOR):
        return True
    return in_group(user, GROUP_BUSINESS_OWNER) and use_case.business_owner_id == user.id


def can_confirm_go_live_exception(user) -> bool:
    """Allow a failed-pilot go-live exception only to the explicit coordinator group."""

    return bool(user and user.is_authenticated and in_group(user, GROUP_COORDINATOR))
