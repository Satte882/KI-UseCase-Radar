from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from .architecture_artifacts import get_delivery_architecture_artifacts
from .models import DELIVERY_SECTION_DEFINITIONS, DeliveryPackage, DeliverySectionReview


@dataclass(frozen=True)
class ReadinessFinding:
    section_key: str
    code: str
    severity: str
    message: str


SECTION_LABELS = dict(DELIVERY_SECTION_DEFINITIONS)
READY_REQUIRED_FIELDS = {
    "problem_and_target": (
        "problem_context",
        "target_outcome",
    ),
    "scope_and_users": (
        "in_scope",
        "out_of_scope",
        "users_and_scenarios",
        "mvp_scope",
    ),
    "solution_direction": (
        "solution_outline",
        "architecture_decisions",
    ),
    "architecture_and_data": (
        "system_context",
        "data_context",
        "integrations",
    ),
    "requirements_and_governance": (
        "functional_requirements",
        "non_functional_requirements",
        "security_privacy_requirements",
        "human_oversight",
        "logging_and_audit",
        "operations_and_support",
    ),
    "acceptance_and_measurement": (
        "acceptance_criteria",
        "test_scenarios",
        "measurement_plan",
    ),
    "delivery_control": (
        "dependencies",
        "risks",
        "assumptions",
        "initial_backlog",
        "external_delivery_url",
        "handover_notes",
    ),
}

ARCHITECTURE_REQUIRED_FIELDS = {
    "system_landscape": "Ist-/Ziel-Systemlandschaft",
    "system_responsibilities": "Systemverantwortung und Zielkomponenten",
    "data_flows": "Daten- und Informationsflüsse",
    "data_quality_and_access": "Datenqualität, Zugriff und Schutzbedarf",
    "integration_contracts": "Integrationsverträge und Verantwortlichkeiten",
    "integration_operations": "Integrationsbetrieb und Fehlerbehandlung",
}

GENERIC_PLACEHOLDER_FRAGMENTS = (
    "im delivery package konkretisieren",
    "konkretisieren.",
    "explizit ergänzen",
    "ergänzen.",
    "kleinsten ende-zu-ende-ablauf",
    "kernablauf aus dem freigegebenen use case umsetzen",
    "fachliche entscheidung und ergebnis nachvollziehbar darstellen",
    "happy path, datenfehler, fachliche ausnahme",
    "epic 1: kernprozess und nutzerfluss",
    "keine zusätzlichen prüfungen markiert",
    "fachliche verantwortlichkeiten bestätigen",
)


def _text(value) -> str:
    return str(value or "").strip()


def _field_label(package: DeliveryPackage, field_name: str) -> str:
    return str(package._meta.get_field(field_name).verbose_name)


def _is_generic_placeholder(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in GENERIC_PLACEHOLDER_FRAGMENTS)


def _parse_manifest_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _source_staleness_findings(
    package: DeliveryPackage,
    reviews_by_key,
) -> list[ReadinessFinding]:
    review = reviews_by_key.get("problem_and_target")
    if review is None or not review.source_manifest:
        return []

    manifest = review.source_manifest
    findings: list[ReadinessFinding] = []
    source_objects = [("use_case", package.use_case)]
    try:
        origin = package.use_case.architecture_origin
    except ObjectDoesNotExist:
        origin = None
    if origin is not None:
        source_objects.extend(
            [
                ("value_stream", origin.stage.value_stream),
                ("process_analysis", origin.process_analysis),
                ("solution_option", origin.solution_option),
            ]
        )
    source_objects.extend(
        [
            ("assessment", package.generated_from_decision.assessment),
            ("approval", package.generated_from_decision),
        ]
    )

    for key, source in source_objects:
        if source is None or not hasattr(source, "updated_at"):
            continue
        recorded = _parse_manifest_time((manifest.get(key) or {}).get("updated_at"))
        current = source.updated_at
        if recorded and current and current > recorded:
            findings.append(
                ReadinessFinding(
                    "delivery_control",
                    "SOURCE_CHANGED_AFTER_SNAPSHOT",
                    "warning",
                    f"Die Quelle „{key}“ wurde nach Erzeugung dieser Package-Version geändert.",
                )
            )
    return findings


def evaluate_delivery_readiness(package: DeliveryPackage) -> list[ReadinessFinding]:
    if package.readiness_schema_version < 2:
        return []

    findings: list[ReadinessFinding] = []
    if package.use_case.technical_owner_id is None:
        findings.append(
            ReadinessFinding(
                "architecture_and_data",
                "TECHNICAL_OWNER_MISSING",
                "blocker",
                "Vor der Übergabe muss ein Technical Owner benannt sein.",
            )
        )

    reviews = {review.section_key: review for review in package.section_reviews.all()}
    for section_key, section_label in DELIVERY_SECTION_DEFINITIONS:
        review = reviews.get(section_key)
        if review is None:
            findings.append(
                ReadinessFinding(
                    section_key,
                    "SECTION_REVIEW_MISSING",
                    "blocker",
                    f"Für „{section_label}“ fehlt die strukturierte Sektionsprüfung.",
                )
            )
            continue
        if not review.source_manifest:
            findings.append(
                ReadinessFinding(
                    section_key,
                    "SOURCE_MANIFEST_MISSING",
                    "blocker",
                    f"Für „{section_label}“ fehlt der Quellenstand.",
                )
            )
        if review.review_status == DeliverySectionReview.ReviewStatus.BLOCKED:
            findings.append(
                ReadinessFinding(
                    section_key,
                    "SECTION_BLOCKED",
                    "blocker",
                    review.review_note or f"Die Sektion „{section_label}“ ist blockiert.",
                )
            )
        elif review.review_status == DeliverySectionReview.ReviewStatus.NEEDS_REVIEW:
            findings.append(
                ReadinessFinding(
                    section_key,
                    "SECTION_NEEDS_REVIEW",
                    "blocker",
                    f"Die Sektion „{section_label}“ wurde noch nicht vollständig bestätigt.",
                )
            )
        elif review.review_status == DeliverySectionReview.ReviewStatus.NOT_APPLICABLE:
            if not _text(review.review_note):
                findings.append(
                    ReadinessFinding(
                        section_key,
                        "NOT_APPLICABLE_REASON_MISSING",
                        "blocker",
                        f"Für „{section_label}“ fehlt die Begründung der Nichtanwendbarkeit.",
                    )
                )
        elif not review.confirmations_complete:
            findings.append(
                ReadinessFinding(
                    section_key,
                    "REQUIRED_CONFIRMATION_MISSING",
                    "blocker",
                    (
                        f"Für „{section_label}“ fehlen erforderliche fachliche oder "
                        "technische Bestätigungen."
                    ),
                )
            )

    for section_key, field_names in READY_REQUIRED_FIELDS.items():
        for field_name in field_names:
            value = _text(getattr(package, field_name, ""))
            label = _field_label(package, field_name)
            if not value:
                findings.append(
                    ReadinessFinding(
                        section_key,
                        f"{field_name.upper()}_MISSING",
                        "blocker",
                        f"Pflichtangabe fehlt: {label}.",
                    )
                )
            elif _is_generic_placeholder(value):
                findings.append(
                    ReadinessFinding(
                        section_key,
                        f"{field_name.upper()}_GENERIC",
                        "blocker",
                        (
                            f"Die Angabe „{label}“ ist noch eine generische Vorlage und "
                            "muss konkretisiert werden."
                        ),
                    )
                )

    artifacts = get_delivery_architecture_artifacts(package)
    if artifacts is None:
        findings.append(
            ReadinessFinding(
                "architecture_and_data",
                "ARCHITECTURE_ARTIFACTS_MISSING",
                "blocker",
                "Die umsetzungsbezogenen Architekturartefakte fehlen.",
            )
        )
    else:
        for field_name, label in ARCHITECTURE_REQUIRED_FIELDS.items():
            value = _text(getattr(artifacts, field_name, ""))
            if not value:
                findings.append(
                    ReadinessFinding(
                        "architecture_and_data",
                        f"{field_name.upper()}_MISSING",
                        "blocker",
                        f"Pflichtangabe fehlt: {label}.",
                    )
                )
            elif _is_generic_placeholder(value):
                findings.append(
                    ReadinessFinding(
                        "architecture_and_data",
                        f"{field_name.upper()}_GENERIC",
                        "blocker",
                        (
                            f"Die Angabe „{label}“ ist noch eine generische Vorlage und "
                            "muss konkretisiert werden."
                        ),
                    )
                )

    decision = package.generated_from_decision
    if _text(decision.conditions):
        if decision.condition_owner_id is None:
            findings.append(
                ReadinessFinding(
                    "delivery_control",
                    "CONDITION_OWNER_MISSING",
                    "blocker",
                    "Die Freigabe enthält Auflagen, aber keinen verantwortlichen Condition Owner.",
                )
            )
        if decision.condition_due_date is None:
            findings.append(
                ReadinessFinding(
                    "delivery_control",
                    "CONDITION_DUE_DATE_MISSING",
                    "blocker",
                    "Die Freigabe enthält Auflagen, aber keine Fälligkeit.",
                )
            )
        if decision.conditions.casefold() not in package.handover_notes.casefold():
            findings.append(
                ReadinessFinding(
                    "delivery_control",
                    "APPROVAL_CONDITIONS_NOT_TRANSFERRED",
                    "blocker",
                    (
                        "Die verbindlichen Freigabeauflagen wurden nicht vollständig in die "
                        "Übergabehinweise übernommen."
                    ),
                )
            )

    findings.extend(_source_staleness_findings(package, reviews))
    return findings


def blocking_findings(package: DeliveryPackage) -> list[ReadinessFinding]:
    return [
        finding for finding in evaluate_delivery_readiness(package) if finding.severity == "blocker"
    ]


def _legacy_missing_ready_fields(package: DeliveryPackage) -> list[str]:
    legacy_fields = (
        "problem_context",
        "target_outcome",
        "in_scope",
        "out_of_scope",
        "users_and_scenarios",
        "solution_outline",
        "system_context",
        "data_context",
        "functional_requirements",
        "non_functional_requirements",
        "security_privacy_requirements",
        "human_oversight",
        "logging_and_audit",
        "operations_and_support",
        "mvp_scope",
        "acceptance_criteria",
        "test_scenarios",
        "measurement_plan",
        "initial_backlog",
        "integrations",
        "dependencies",
        "risks",
        "assumptions",
        "architecture_decisions",
    )
    missing = [
        _field_label(package, field_name)
        for field_name in legacy_fields
        if not _text(getattr(package, field_name, ""))
    ]
    artifacts = get_delivery_architecture_artifacts(package)
    if artifacts is None:
        missing.extend(
            [
                "Ist-/Ziel-Systemlandschaft",
                "Daten- und Informationsflüsse",
                "Integrationsverträge und Verantwortlichkeiten",
            ]
        )
    else:
        legacy_artifact_fields = {
            "system_landscape": "Ist-/Ziel-Systemlandschaft",
            "data_flows": "Daten- und Informationsflüsse",
            "integration_contracts": "Integrationsverträge und Verantwortlichkeiten",
        }
        for field_name, label in legacy_artifact_fields.items():
            if not _text(getattr(artifacts, field_name, "")):
                missing.append(label)
    return list(dict.fromkeys(missing))


def missing_ready_fields(package: DeliveryPackage) -> list[str]:
    if package.readiness_schema_version < 2:
        return _legacy_missing_ready_fields(package)
    return [finding.message for finding in blocking_findings(package)]


def render_delivery_markdown(package: DeliveryPackage) -> str:
    """Compatibility wrapper for callers of the former readiness export."""

    from .exports import render_delivery_markdown as render

    return render(package)
