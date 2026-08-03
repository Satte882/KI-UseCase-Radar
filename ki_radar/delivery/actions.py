from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse

from ki_radar.accounts.permissions import is_coordinator
from ki_radar.core.navigation import with_return_to
from ki_radar.use_cases.permissions import can_edit_use_case

from .models import DELIVERY_SECTION_DEFINITIONS, SECTION_REVIEW_REQUIREMENTS, DeliveryPackage
from .permissions import allowed_edit_sections, can_review_section
from .readiness import (
    ARCHITECTURE_REQUIRED_FIELDS,
    READY_REQUIRED_FIELDS,
    ReadinessFinding,
    evaluate_delivery_readiness,
)

SECTION_LABELS = dict(DELIVERY_SECTION_DEFINITIONS)
SECTION_ORDER = {key: index for index, (key, _label) in enumerate(DELIVERY_SECTION_DEFINITIONS)}
PACKAGE_FIELD_ORDER = {
    field_name: index
    for index, field_name in enumerate(
        field_name
        for section_key, _label in DELIVERY_SECTION_DEFINITIONS
        for field_name in READY_REQUIRED_FIELDS[section_key]
    )
}
ARCHITECTURE_FIELD_ORDER = {
    field_name: len(PACKAGE_FIELD_ORDER) + index
    for index, field_name in enumerate(ARCHITECTURE_REQUIRED_FIELDS)
}
FIELD_ORDER = PACKAGE_FIELD_ORDER | ARCHITECTURE_FIELD_ORDER
PACKAGE_FIELD_CODES = {
    f"{field_name.upper()}_{suffix}": field_name
    for field_name in PACKAGE_FIELD_ORDER
    for suffix in ("MISSING", "GENERIC")
}
ARCHITECTURE_FIELD_CODES = {
    f"{field_name.upper()}_{suffix}": field_name
    for field_name in ARCHITECTURE_FIELD_ORDER
    for suffix in ("MISSING", "GENERIC")
}
FIELD_CODES = PACKAGE_FIELD_CODES | ARCHITECTURE_FIELD_CODES

RESPONSIBILITY_CODES = {
    "TECHNICAL_OWNER_MISSING",
    "TECHNICAL_OWNER_INACTIVE",
}
STRUCTURE_CODES = {
    "SECTION_REVIEW_MISSING",
    "SOURCE_MANIFEST_MISSING",
    "ARCHITECTURE_ARTIFACTS_MISSING",
}
REVIEW_CODES = {
    "SECTION_BLOCKED",
    "SECTION_NEEDS_REVIEW",
    "REQUIRED_CONFIRMATION_MISSING",
    "NOT_APPLICABLE_REASON_MISSING",
}
CONDITION_CODES = {
    "CONDITION_OWNER_MISSING",
    "CONDITION_DUE_DATE_MISSING",
    "APPROVAL_CONDITIONS_NOT_TRANSFERRED",
}


@dataclass(frozen=True)
class ActionableFinding:
    code: str
    section_key: str
    severity: str
    message: str
    title: str
    priority_class: int
    action_label: str
    url: str
    responsible_role: str
    responsible_person: str
    can_execute: bool
    field_name: str = ""

    @property
    def sort_key(self) -> tuple[int, int, int, str]:
        return (
            self.priority_class,
            SECTION_ORDER.get(self.section_key, 99),
            FIELD_ORDER.get(self.field_name, 999),
            self.code,
        )


def _display_name(user) -> str:
    return user.get_display_name() if user else "Nicht benannt"


def section_responsibility(package: DeliveryPackage, section_key: str) -> tuple[str, str]:
    requirements = SECTION_REVIEW_REQUIREMENTS.get(section_key, frozenset())
    business_owner = package.use_case.business_owner
    technical_owner = package.use_case.technical_owner

    if requirements == {"business"}:
        return "Business Owner", _display_name(business_owner)
    if requirements == {"technical"}:
        return "Technical Owner (Technik, Daten und KI)", _display_name(technical_owner)
    if requirements == {"business", "technical"}:
        if technical_owner and technical_owner.pk == business_owner.pk:
            return (
                "Business Owner sowie Technical Owner (Technik, Daten und KI)",
                _display_name(business_owner),
            )
        return (
            "Business Owner und Technical Owner (Technik, Daten und KI)",
            f"{_display_name(business_owner)} / {_display_name(technical_owner)}",
        )
    return "KI-Koordinator", "Berechtigte Koordination"


def _priority(code: str, severity: str) -> int:
    if code in RESPONSIBILITY_CODES:
        return 1
    if code in STRUCTURE_CODES:
        return 2
    if code in FIELD_CODES or code in CONDITION_CODES:
        return 3
    if code in REVIEW_CODES:
        return 4
    if severity == "warning":
        return 6
    return 3


def _field_label(package: DeliveryPackage, field_name: str) -> str:
    if field_name in ARCHITECTURE_REQUIRED_FIELDS:
        return ARCHITECTURE_REQUIRED_FIELDS[field_name]
    return str(package._meta.get_field(field_name).verbose_name)


def _package_edit_url(package: DeliveryPackage, field_name: str, return_to: str) -> str:
    base = reverse("delivery:package_update", kwargs={"pk": package.pk})
    target = f"{base}?{urlencode({'highlight': field_name})}#field-{field_name}"
    return with_return_to(target, return_to)


def _use_case_edit_url(package: DeliveryPackage, field_name: str, return_to: str) -> str:
    base = reverse("use_cases:edit", kwargs={"pk": package.use_case.pk})
    target = f"{base}?{urlencode({'highlight': field_name})}#field-{field_name}"
    return with_return_to(target, return_to)


def _synthetic_findings(package: DeliveryPackage) -> list[ReadinessFinding]:
    findings: list[ReadinessFinding] = []
    technical_owner = package.use_case.technical_owner
    if technical_owner is not None and not technical_owner.is_active:
        findings.append(
            ReadinessFinding(
                "architecture_and_data",
                "TECHNICAL_OWNER_INACTIVE",
                "blocker",
                (
                    "Der zugeordnete Technical Owner ist nicht aktiv und kann die "
                    "technische Verantwortung nicht wahrnehmen."
                ),
            )
        )

    return findings


def _build_action(
    package: DeliveryPackage,
    finding: ReadinessFinding,
    user,
    *,
    return_to: str,
) -> ActionableFinding:
    code = finding.code
    section_key = finding.section_key
    responsible_role, responsible_person = section_responsibility(package, section_key)
    priority_class = _priority(code, finding.severity)
    title = finding.message
    action_label = ""
    url = ""
    can_execute = False
    field_name = FIELD_CODES.get(code, "")

    if code in {"TECHNICAL_OWNER_MISSING", "TECHNICAL_OWNER_INACTIVE"}:
        title = (
            "Technical Owner benennen" if code.endswith("MISSING") else "Technical Owner ersetzen"
        )
        action_label = "Technical Owner zuordnen"
        responsible_role = "Business Owner oder KI-Koordinator"
        responsible_person = _display_name(package.use_case.business_owner)
        can_execute = can_edit_use_case(user, package.use_case)
        if can_execute:
            url = _use_case_edit_url(package, "technical_owner", return_to)
    elif field_name:
        label = _field_label(package, field_name)
        title = f"{label} {'konkretisieren' if code.endswith('GENERIC') else 'ergänzen'}"
        action_label = "Feld bearbeiten"
        can_execute = section_key in allowed_edit_sections(user, package)
        if can_execute:
            url = _package_edit_url(package, field_name, return_to)
    elif code in REVIEW_CODES:
        label = SECTION_LABELS.get(section_key, section_key)
        title = (
            f"Begründung für „{label}“ ergänzen"
            if code == "NOT_APPLICABLE_REASON_MISSING"
            else f"Unabhängige Kontrolle für „{label}“ durchführen"
            if code == "INDEPENDENT_CONFIRMATION_MISSING"
            else f"Sektion „{label}“ prüfen"
        )
        action_label = "Sektion prüfen"
        can_execute = can_review_section(user, package, section_key)
        if can_execute:
            url = f"{package.get_absolute_url()}#section-{section_key}"
    elif code == "ARCHITECTURE_ARTIFACTS_MISSING":
        title = "Architekturkontext anlegen"
        action_label = "Architekturkontext bearbeiten"
        responsible_role, responsible_person = section_responsibility(
            package, "architecture_and_data"
        )
        can_execute = "architecture_and_data" in allowed_edit_sections(user, package)
        if can_execute:
            url = _package_edit_url(package, "system_landscape", return_to)
    elif code in {"SECTION_REVIEW_MISSING", "SOURCE_MANIFEST_MISSING"}:
        label = SECTION_LABELS.get(section_key, section_key)
        title = f"Struktur für „{label}“ wiederherstellen"
        action_label = "Readiness öffnen"
        responsible_role = "KI-Koordinator"
        responsible_person = "Berechtigte Koordination"
        can_execute = is_coordinator(user)
        if can_execute:
            url = f"{package.get_absolute_url()}#section-{section_key}"
    elif code in {"CONDITION_OWNER_MISSING", "CONDITION_DUE_DATE_MISSING"}:
        title = "Freigabeauflage vervollständigen"
        action_label = "Freigabe prüfen"
        responsible_role = "KI-Koordinator"
        responsible_person = "Berechtigte Koordination"
        can_execute = is_coordinator(user)
        if can_execute:
            url = f"{package.use_case.get_absolute_url()}#approval"
    elif code == "APPROVAL_CONDITIONS_NOT_TRANSFERRED":
        title = "Freigabeauflagen in die Übergabe übernehmen"
        action_label = "Übergabehinweise bearbeiten"
        can_execute = "delivery_control" in allowed_edit_sections(user, package)
        if can_execute:
            url = _package_edit_url(package, "handover_notes", return_to)
    elif code == "SOURCE_CHANGED_AFTER_SNAPSHOT":
        title = "Geänderte Quelle prüfen"
        action_label = "Use Case öffnen"
        responsible_role = "KI-Koordinator"
        responsible_person = "Berechtigte Koordination"
        can_execute = is_coordinator(user)
        if can_execute:
            url = package.use_case.get_absolute_url()
    return ActionableFinding(
        code=code,
        section_key=section_key,
        severity=finding.severity,
        message=finding.message,
        title=title,
        priority_class=priority_class,
        action_label=action_label,
        url=url,
        responsible_role=responsible_role,
        responsible_person=responsible_person,
        can_execute=can_execute,
        field_name=field_name,
    )


def build_actionable_findings(
    package: DeliveryPackage,
    user,
    *,
    return_to: str | None = None,
) -> list[ActionableFinding]:
    target = return_to or package.get_absolute_url()
    raw_findings = [*evaluate_delivery_readiness(package), *_synthetic_findings(package)]
    actions = [_build_action(package, finding, user, return_to=target) for finding in raw_findings]
    return sorted(actions, key=lambda item: item.sort_key)


def primary_delivery_action(
    package: DeliveryPackage,
    user,
    *,
    return_to: str | None = None,
) -> ActionableFinding | None:
    return next(
        (
            finding
            for finding in build_actionable_findings(package, user, return_to=return_to)
            if finding.severity == "blocker"
        ),
        None,
    )
