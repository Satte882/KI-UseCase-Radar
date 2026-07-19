from ki_radar.accounts.permissions import is_business_owner, is_coordinator


def can_create_use_case(user) -> bool:
    return is_business_owner(user)


def can_edit_use_case(user, use_case) -> bool:
    return is_coordinator(user) or (is_business_owner(user) and use_case.business_owner_id == user.id)


def can_view_use_case(user, use_case) -> bool:
    return user.is_authenticated and not use_case.is_archived
