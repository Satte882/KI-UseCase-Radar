from ki_radar.accounts.permissions import is_coordinator
from ki_radar.use_cases.permissions import can_view_use_case

from .models import DeliveryPackage

BUSINESS_SECTIONS = {
    "problem_and_target",
    "scope_and_users",
    "solution_direction",
    "acceptance_and_measurement",
    "delivery_control",
}
TECHNICAL_SECTIONS = {
    "solution_direction",
    "architecture_and_data",
    "requirements_and_governance",
    "delivery_control",
}


def can_view_package(user, package: DeliveryPackage) -> bool:
    return can_view_use_case(user, package.use_case)


def can_create_package(user) -> bool:
    return is_coordinator(user)


def allowed_edit_sections(user, package: DeliveryPackage) -> set[str]:
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        return set()
    if is_coordinator(user):
        return BUSINESS_SECTIONS | TECHNICAL_SECTIONS

    allowed: set[str] = set()
    if package.use_case.business_owner_id == user.id:
        allowed |= BUSINESS_SECTIONS
    if package.use_case.technical_owner_id == user.id:
        allowed |= TECHNICAL_SECTIONS
    return allowed


def can_edit_package(user, package: DeliveryPackage) -> bool:
    return bool(allowed_edit_sections(user, package))


def can_review_section(user, package: DeliveryPackage, section_key: str) -> bool:
    return section_key in allowed_edit_sections(user, package)


def reviewer_roles(user, package: DeliveryPackage, section_key: str) -> set[str]:
    if is_coordinator(user):
        return {"business", "technical"}

    roles: set[str] = set()
    if package.use_case.business_owner_id == user.id and section_key in BUSINESS_SECTIONS:
        roles.add("business")
    if package.use_case.technical_owner_id == user.id and section_key in TECHNICAL_SECTIONS:
        roles.add("technical")
    return roles


def can_transition_package(user) -> bool:
    return is_coordinator(user)
