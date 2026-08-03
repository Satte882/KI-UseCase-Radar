from ki_radar.accounts.permissions import is_business_owner, is_coordinator
from ki_radar.use_cases.permissions import can_view_use_case

from .models import DeliveryPackage, DeliverySectionReview

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


def can_confirm_business(user, package: DeliveryPackage, section_key: str) -> bool:
    return bool(
        section_key in BUSINESS_SECTIONS
        and (package.use_case.business_owner_id == user.id or is_business_owner(user))
    )


def can_confirm_technical(user, package: DeliveryPackage, section_key: str) -> bool:
    return bool(
        section_key in TECHNICAL_SECTIONS
        and (package.use_case.technical_owner_id == user.id or is_coordinator(user))
    )


def allowed_edit_sections(user, package: DeliveryPackage) -> set[str]:
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        return set()
    allowed: set[str] = set()
    for section_key in BUSINESS_SECTIONS | TECHNICAL_SECTIONS:
        if can_confirm_business(user, package, section_key) or can_confirm_technical(
            user, package, section_key
        ):
            allowed.add(section_key)
    return allowed


def can_edit_package(user, package: DeliveryPackage) -> bool:
    return bool(allowed_edit_sections(user, package))


def can_review_section(user, package: DeliveryPackage, section_key: str) -> bool:
    return bool(reviewer_roles(user, package, section_key))


def reviewer_roles(user, package: DeliveryPackage, section_key: str) -> set[str]:
    roles: set[str] = set()
    if can_confirm_business(user, package, section_key):
        roles.add("business")
    if can_confirm_technical(user, package, section_key):
        roles.add("technical")
    return roles


def confirmation_role_label(role: str, *, assigned: bool) -> str:
    if role == "business":
        return "Business Owner" if assigned else "Berechtigte fachliche Stellvertretung"
    return "Technical Owner" if assigned else "Berechtigte technische Stellvertretung"


def can_independently_check(
    user,
    package: DeliveryPackage,
    review: DeliverySectionReview,
) -> bool:
    if not review.has_role_collapse or review.business_confirmed_by_id == user.id:
        return False
    return bool(reviewer_roles(user, package, review.section_key))


def can_transition_package(user) -> bool:
    return is_coordinator(user)
