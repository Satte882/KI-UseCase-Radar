from __future__ import annotations

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from ki_radar.use_cases.models import ApprovalDecision, UseCase

from .exports import render_delivery_markdown
from .models import (
    DELIVERY_SECTION_DEFINITIONS,
    DeliveryPackage,
    DeliverySectionReview,
)
from .permissions import (
    can_use_admin_confirmation_override,
    confirmation_role_label,
    reviewer_roles,
)
from .readiness import blocking_findings, missing_ready_fields

APPROVED_STATUSES = {
    UseCase.DecisionStatus.APPROVED,
    UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS,
}

SECTION_ORIGINS = {
    "problem_and_target": DeliverySectionReview.ContentOrigin.INHERITED,
    "scope_and_users": DeliverySectionReview.ContentOrigin.INHERITED,
    "solution_direction": DeliverySectionReview.ContentOrigin.MIXED,
    "architecture_and_data": DeliverySectionReview.ContentOrigin.MIXED,
    "requirements_and_governance": DeliverySectionReview.ContentOrigin.NEW,
    "acceptance_and_measurement": DeliverySectionReview.ContentOrigin.MIXED,
    "delivery_control": DeliverySectionReview.ContentOrigin.MIXED,
}


def latest_final_approval(use_case: UseCase) -> ApprovalDecision | None:
    return (
        use_case.approval_decisions.filter(
            decision_status__in=APPROVED_STATUSES,
            finalized_at__isnull=False,
        )
        .select_related("assessment", "decided_by", "second_approved_by")
        .first()
    )


def current_delivery_package(use_case: UseCase) -> DeliveryPackage | None:
    """Return the latest Delivery Package version for the Use Case."""

    return DeliveryPackage.objects.filter(use_case_id=use_case.pk).first()


def current_handed_over_package(use_case: UseCase) -> DeliveryPackage | None:
    """Return the current package only when its handover is complete and timestamped."""

    package = current_delivery_package(use_case)
    if (
        package is not None
        and package.status == DeliveryPackage.Status.HANDED_OVER
        and package.handed_over_at is not None
    ):
        return package
    return None


def delivery_eligibility(use_case: UseCase) -> tuple[bool, str, ApprovalDecision | None]:
    if use_case.decision_status not in APPROVED_STATUSES:
        return False, "Der Use Case besitzt keine finale positive Freigabe.", None
    decision = latest_final_approval(use_case)
    if decision is None:
        return False, "Die positive Freigabe ist noch nicht final dokumentiert.", None
    return True, "", decision


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _source_entry(source, *, version=None) -> dict[str, str | int | None]:
    if source is None:
        return {}
    entry: dict[str, str | int | None] = {
        "id": str(source.pk),
        "updated_at": _iso(getattr(source, "updated_at", None)),
    }
    if version is not None:
        entry["version"] = version
    return entry


def _field_source(*, kind: str, label: str, source, field: str, value=None) -> dict:
    raw_value = getattr(source, field) if value is None else value
    return {
        "kind": kind,
        "label": label,
        "id": str(source.pk),
        "field": field,
        "value": "" if raw_value is None else str(raw_value),
        "updated_at": _iso(getattr(source, "updated_at", None)),
    }


def _origin_context(use_case: UseCase):
    try:
        origin = use_case.architecture_origin
    except ObjectDoesNotExist:
        return None, None, None
    return origin, origin.process_analysis, origin.solution_option


def build_delivery_field_sources(use_case: UseCase) -> dict[str, dict]:
    origin, _process, _option = _origin_context(use_case)
    sources = {
        "problem_context": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="problem_statement",
        ),
        "target_outcome": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="expected_benefit",
        ),
        "users_and_scenarios": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="intended_users" if use_case.intended_users else "target_users",
        ),
        "solution_outline": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="intended_purpose" if use_case.intended_purpose else "summary",
        ),
        "system_context": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="source_systems",
        ),
        "data_context": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="data_sources",
        ),
        "integrations": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="interface_description",
        ),
        "human_oversight": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="human_oversight",
        ),
        "operations_and_support": _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="support_responsibility",
        ),
    }
    if origin is not None:
        sources["in_scope"] = _field_source(
            kind="value_stream",
            label="Value Stream",
            source=origin.stage.value_stream,
            field="scope_in",
        )
        sources["out_of_scope"] = _field_source(
            kind="value_stream",
            label="Value Stream",
            source=origin.stage.value_stream,
            field="scope_out",
        )
    else:
        sources["in_scope"] = _field_source(
            kind="use_case",
            label="Use Case",
            source=use_case,
            field="summary" if use_case.summary else "affected_process",
        )
    return sources


def build_source_manifest(use_case: UseCase, decision: ApprovalDecision) -> dict:
    origin, process, option = _origin_context(use_case)
    manifest = {
        "use_case": _source_entry(use_case),
        "assessment": _source_entry(decision.assessment, version=decision.assessment.version),
        "approval": _source_entry(decision),
        "field_sources": build_delivery_field_sources(use_case),
        "role_sources": {
            "business_owner": {
                "id": str(use_case.business_owner_id or ""),
                "value": str(use_case.business_owner or ""),
            },
            "technical_owner": {
                "id": str(use_case.technical_owner_id or ""),
                "value": str(use_case.technical_owner or ""),
            },
        },
    }
    if origin is not None:
        manifest.update(
            {
                "value_stream": _source_entry(origin.stage.value_stream),
                "value_stream_stage": _source_entry(origin.stage),
                "process_analysis": _source_entry(process),
                "solution_option": _source_entry(option),
            }
        )
    return manifest


def _current_source_objects(use_case: UseCase) -> dict:
    origin, process, option = _origin_context(use_case)
    return {
        "use_case": use_case,
        "value_stream": origin.stage.value_stream if origin is not None else None,
        "value_stream_stage": origin.stage if origin is not None else None,
        "process_analysis": process,
        "solution_option": option,
    }


def delivery_source_differences(package: DeliveryPackage) -> list[dict]:
    review = package.section_reviews.filter(section_key="problem_and_target").first()
    if review is None:
        return []
    objects = _current_source_objects(package.use_case)
    differences = []
    for package_field, source in (review.source_manifest.get("field_sources") or {}).items():
        obj = objects.get(source.get("kind"))
        source_field = source.get("field")
        if obj is None or not source_field:
            continue
        current = getattr(obj, source_field, None)
        current_text = "" if current is None else str(current)
        snapshot_text = str(source.get("value") or "")
        differences.append(
            {
                "package_field": package_field,
                "package_label": str(package._meta.get_field(package_field).verbose_name),
                "source_label": source.get("label", "Quelle"),
                "source_field": source_field,
                "snapshot": snapshot_text,
                "current": current_text,
                "changed": current_text != snapshot_text,
            }
        )
    return differences


def _architecture_artifacts_payload(
    use_case: UseCase,
    decision: ApprovalDecision,
) -> dict[str, str]:
    _origin, _process, option = _origin_context(use_case)
    systems = use_case.source_systems
    data_objects = use_case.data_sources
    application_impact = option.application_impact if option else ""
    integration_impact = use_case.interface_description
    technical_owner = use_case.technical_owner
    business_owner = use_case.business_owner

    target_components = application_impact or "Zielkomponenten im Delivery Package konkretisieren."
    system_responsibility = (
        f"Fachlicher Owner: {business_owner}\n"
        f"Technischer Owner: {technical_owner or 'noch nicht benannt'}\n"
        "Führendes System/System of Record: konkretisieren.\n"
        f"Zu ändernde oder neue Komponenten: {target_components}"
    )
    data_readiness = decision.assessment.get_data_readiness_display()
    return {
        "system_landscape": (
            f"Ist-Systeme und Arbeitsmittel:\n{systems or 'Noch nicht dokumentiert.'}\n\n"
            f"Zielkomponenten und Anwendungsauswirkungen:\n{target_components}"
        ),
        "system_responsibilities": system_responsibility,
        "data_flows": (
            f"Datenobjekte und Quellen:\n{data_objects or 'Noch nicht dokumentiert.'}\n\n"
            f"Integrationen:\n{integration_impact or 'Noch zu konkretisieren.'}"
        ),
        "data_quality_and_access": (
            f"Bewertete Datenreife: {data_readiness}\n"
            "Zugriffsweg, Datenverantwortung, bekannte Qualitätsprobleme, Schutzbedarf und "
            "Aktualisierung konkretisieren."
        ),
        "integration_contracts": integration_impact or "Integrationsvertrag konkretisieren.",
        "integration_operations": (
            "Authentifizierung, Auslöser/Frequenz, Fehlerbehandlung, Retry/Fallback, Logging, "
            "Monitoring und technische Verantwortung konkretisieren."
        ),
        "artifacts_url": "",
    }


def build_initial_delivery_data(
    use_case: UseCase,
    decision: ApprovalDecision,
) -> dict[str, str]:
    origin, _process, _option = _origin_context(use_case)
    metric = (
        f"{use_case.metric_name}: Baseline {use_case.metric_baseline} "
        f"→ Ziel {use_case.metric_target} {use_case.metric_unit}.\n"
        f"Messmethode: {use_case.metric_measurement_method}\n"
        f"Messzeitraum: {use_case.metric_measurement_period or 'für den Pilot festlegen'}"
        if use_case.metric_name
        else "Erfolgsmessung im Delivery Package konkretisieren."
    )
    checks = []
    if use_case.privacy_review_required:
        checks.append("Datenschutzprüfung erforderlich")
    if use_case.security_review_required:
        checks.append("Informationssicherheitsprüfung erforderlich")
    if use_case.legal_review_required:
        checks.append("Rechtsprüfung erforderlich")

    condition_lines = [
        f"Freigabe: {decision.get_decision_status_display()}",
        f"Begründung: {decision.rationale}",
    ]
    if decision.conditions:
        condition_lines.extend(
            [
                f"Auflagen: {decision.conditions}",
                f"Auflagenverantwortung: {decision.condition_owner or 'nicht benannt'}",
                f"Fälligkeit: {decision.condition_due_date or 'nicht festgelegt'}",
            ]
        )
    else:
        condition_lines.append("Keine Auflagen.")

    value_stream = origin.stage.value_stream if origin is not None else None
    return {
        "problem_context": use_case.problem_statement,
        "target_outcome": use_case.expected_benefit,
        "in_scope": (
            value_stream.scope_in
            if value_stream is not None
            else use_case.summary or use_case.affected_process
        ),
        "out_of_scope": value_stream.scope_out if value_stream is not None else "",
        "users_and_scenarios": use_case.intended_users or use_case.target_users,
        "solution_outline": use_case.intended_purpose or use_case.summary,
        "system_context": use_case.source_systems,
        "data_context": use_case.data_sources,
        "integrations": use_case.interface_description,
        "functional_requirements": (
            "1. Kernablauf aus dem freigegebenen Use Case umsetzen.\n"
            "2. Fachliche Entscheidung und Ergebnis nachvollziehbar darstellen."
        ),
        "non_functional_requirements": (
            "Performance, Verfügbarkeit, Barrierefreiheit und Wartbarkeit konkretisieren."
        ),
        "security_privacy_requirements": (
            "\n".join(checks) or "Keine zusätzlichen Prüfungen markiert."
        ),
        "human_oversight": use_case.human_oversight or "Menschliche Kontrolle konkretisieren.",
        "logging_and_audit": (
            "Fachliche Entscheidungen, Fehler und relevante Änderungen protokollieren."
        ),
        "operations_and_support": (
            use_case.support_responsibility or "Betriebsverantwortung festlegen."
        ),
        "mvp_scope": "Kleinsten Ende-zu-Ende-Ablauf für die Nutzenvalidierung beschreiben.",
        "acceptance_criteria": (
            "1. Fachlicher Kernablauf ist Ende-zu-Ende demonstrierbar.\n"
            "2. Freigabeauflagen und Governance-Anforderungen sind umgesetzt.\n"
            f"3. {metric}"
        ),
        "test_scenarios": (
            "Happy Path, Datenfehler, fachliche Ausnahme und manuellen Eingriff testen."
        ),
        "measurement_plan": metric,
        "dependencies": "",
        "risks": (
            f"Bewertung: Risiko/Komplexität {decision.assessment.get_risk_complexity_display()}."
        ),
        "assumptions": "",
        "architecture_decisions": "",
        "initial_backlog": (
            "Epic 1: Kernprozess und Nutzerfluss\n"
            "Epic 2: Daten und Integrationen\n"
            "Epic 3: Governance, Betrieb und Erfolgsmessung"
        ),
        "external_delivery_url": "",
        "handover_notes": "\n".join(condition_lines),
    }

def _create_section_reviews(package: DeliveryPackage, manifest: dict) -> None:
    DeliverySectionReview.objects.bulk_create(
        [
            DeliverySectionReview(
                delivery_package=package,
                section_key=section_key,
                content_origin=SECTION_ORIGINS[section_key],
                review_status=DeliverySectionReview.ReviewStatus.NEEDS_REVIEW,
                source_manifest=manifest,
            )
            for section_key, _ in DELIVERY_SECTION_DEFINITIONS
        ]
    )


@transaction.atomic
def create_delivery_package(*, use_case: UseCase, actor) -> DeliveryPackage:
    eligible, reason, decision = delivery_eligibility(use_case)
    if not eligible or decision is None:
        raise ValidationError(reason)
    version = (
        use_case.delivery_packages.aggregate(max_version=Max("version"))["max_version"] or 0
    ) + 1
    package = DeliveryPackage(
        use_case=use_case,
        version=version,
        generated_from_decision=decision,
        created_by=actor,
        readiness_schema_version=2,
        **build_initial_delivery_data(use_case, decision),
    )
    package._architecture_artifacts_payload = _architecture_artifacts_payload(use_case, decision)
    package.save()
    _create_section_reviews(package, build_source_manifest(use_case, decision))
    return package


@transaction.atomic
def reset_section_reviews(package: DeliveryPackage, section_keys: set[str]) -> None:
    package.section_reviews.filter(section_key__in=section_keys).update(
        review_status=DeliverySectionReview.ReviewStatus.NEEDS_REVIEW,
        reviewed_by=None,
        reviewed_at=None,
        business_confirmed_by=None,
        business_confirmed_at=None,
        technical_confirmed_by=None,
        technical_confirmed_at=None,
        business_confirmation_role="",
        technical_confirmation_role="",
        role_collapse_reason="",
        admin_override_confirmed=False,
    )
    if package.status == DeliveryPackage.Status.READY:
        package.status = DeliveryPackage.Status.DRAFT
        package.save(update_fields=["status", "updated_at"])


@transaction.atomic
def review_delivery_section(
    *,
    package: DeliveryPackage,
    section_key: str,
    action: str,
    actor,
    note: str = "",
    role_collapse_reason: str = "",
) -> DeliverySectionReview:
    try:
        review = package.section_reviews.select_for_update().get(section_key=section_key)
    except DeliverySectionReview.DoesNotExist as exc:
        raise ValidationError("Die angeforderte Delivery-Sektion existiert nicht.") from exc

    roles = reviewer_roles(actor, package, section_key)
    if not roles:
        raise ValidationError("Für diese Sektionsprüfung fehlt die erforderliche Rolle.")

    if action == "confirm":
        open_roles = [
            role
            for role in ("business", "technical")
            if role in roles
            and role in review.required_confirmations
            and getattr(review, f"{role}_confirmed_at") is None
        ]
        if len(open_roles) != 1:
            raise ValidationError(
                "Bitte die fachliche oder technische Bestätigung ausdrücklich auswählen."
            )
        action = f"confirm_{open_roles[0]}"

    now = timezone.now()
    review.reviewed_by = actor
    review.reviewed_at = now
    review.review_note = note.strip()

    if action in {"confirm_business", "confirm_technical"}:
        role = action.removeprefix("confirm_")
        if role not in roles or role not in review.required_confirmations:
            role_label = "fachliche" if role == "business" else "technische"
            raise ValidationError(f"Für die {role_label} Bestätigung fehlt die Berechtigung.")

        other_role = "technical" if role == "business" else "business"
        other_actor_id = getattr(review, f"{other_role}_confirmed_by_id")
        if other_actor_id == actor.id:
            if not can_use_admin_confirmation_override(actor):
                raise ValidationError(
                    "Dieselbe Person darf fachlich und technisch nur als Technischer "
                    "Administrator für Admin- oder Testzwecke bestätigen."
                )
            collapse_reason = role_collapse_reason.strip()
            if not collapse_reason:
                raise ValidationError(
                    "Für die Admin-Sonderbestätigung ist eine Begründung erforderlich."
                )
            review.role_collapse_reason = collapse_reason
            review.admin_override_confirmed = True
        else:
            review.role_collapse_reason = ""
            review.admin_override_confirmed = False

        assigned_owner_id = (
            package.use_case.business_owner_id
            if role == "business"
            else package.use_case.technical_owner_id
        )
        setattr(review, f"{role}_confirmed_by", actor)
        setattr(review, f"{role}_confirmed_at", now)
        setattr(
            review,
            f"{role}_confirmation_role",
            confirmation_role_label(
                role,
                assigned=assigned_owner_id == actor.id,
                admin_override=review.admin_override_confirmed,
            ),
        )
        if review.admin_override_confirmed:
            review.business_confirmation_role = "Admin-Sonderbestätigung"
            review.technical_confirmation_role = "Admin-Sonderbestätigung"
        review.review_status = (
            DeliverySectionReview.ReviewStatus.CONFIRMED
            if review.confirmations_complete
            else DeliverySectionReview.ReviewStatus.NEEDS_REVIEW
        )
    elif action == "block":
        if not review.review_note:
            raise ValidationError("Für eine Blockierung ist eine Begründung erforderlich.")
        review.review_status = DeliverySectionReview.ReviewStatus.BLOCKED
    elif action == "not_applicable":
        if not review.review_note:
            raise ValidationError("Nichtanwendbarkeit muss begründet werden.")
        review.content_origin = DeliverySectionReview.ContentOrigin.NOT_APPLICABLE
        review.review_status = DeliverySectionReview.ReviewStatus.NOT_APPLICABLE
    elif action == "reset":
        review.review_status = DeliverySectionReview.ReviewStatus.NEEDS_REVIEW
        review.business_confirmed_by = None
        review.business_confirmed_at = None
        review.technical_confirmed_by = None
        review.technical_confirmed_at = None
        review.business_confirmation_role = ""
        review.technical_confirmation_role = ""
        review.role_collapse_reason = ""
        review.admin_override_confirmed = False
    else:
        raise ValidationError("Unbekannte Aktion für die Sektionsprüfung.")

    review.save()
    if package.status == DeliveryPackage.Status.READY:
        package.status = DeliveryPackage.Status.DRAFT
        package.save(update_fields=["status", "updated_at"])
    return review


@transaction.atomic
def mark_package_ready(package: DeliveryPackage) -> None:
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        raise ValidationError("Ein übergebenes Delivery Package ist unveränderlich.")
    findings = blocking_findings(package)
    if findings:
        raise ValidationError(
            "Für die Übergabe bestehen noch Blocker: "
            + " | ".join(finding.message for finding in findings)
        )
    package.status = DeliveryPackage.Status.READY
    package.save(update_fields=["status", "updated_at"])


@transaction.atomic
def hand_over_package(package: DeliveryPackage, actor) -> None:
    if package.status != DeliveryPackage.Status.READY:
        raise ValidationError(
            "Nur ein als bereit markiertes Delivery Package kann übergeben werden."
        )
    findings = blocking_findings(package)
    if findings:
        raise ValidationError(
            "Die Readiness-Prüfung ist nicht mehr erfüllt: "
            + " | ".join(finding.message for finding in findings)
        )
    package.status = DeliveryPackage.Status.HANDED_OVER
    package.handed_over_by = actor
    package.handed_over_at = timezone.now()
    package.save(update_fields=["status", "handed_over_by", "handed_over_at", "updated_at"])


__all__ = [
    "APPROVED_STATUSES",
    "build_initial_delivery_data",
    "delivery_source_differences",
    "create_delivery_package",
    "current_delivery_package",
    "current_handed_over_package",
    "delivery_eligibility",
    "hand_over_package",
    "latest_final_approval",
    "mark_package_ready",
    "missing_ready_fields",
    "render_delivery_markdown",
    "reset_section_reviews",
    "review_delivery_section",
]
