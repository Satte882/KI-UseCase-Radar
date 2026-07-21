from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from ki_radar.use_cases.models import ApprovalDecision, UseCase

from .models import DeliveryPackage

APPROVED_STATUSES = {
    UseCase.DecisionStatus.APPROVED,
    UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS,
}
READY_REQUIRED_FIELDS = [
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
]


def latest_final_approval(use_case: UseCase) -> ApprovalDecision | None:
    return (
        use_case.approval_decisions.filter(
            decision_status__in=APPROVED_STATUSES,
            finalized_at__isnull=False,
        )
        .select_related("assessment", "decided_by", "second_approved_by")
        .first()
    )


def delivery_eligibility(use_case: UseCase) -> tuple[bool, str, ApprovalDecision | None]:
    if use_case.decision_status not in APPROVED_STATUSES:
        return False, "Der Use Case besitzt keine finale positive Freigabe.", None
    decision = latest_final_approval(use_case)
    if decision is None:
        return False, "Die positive Freigabe ist noch nicht final dokumentiert.", None
    return True, "", decision


def _architecture_context(use_case: UseCase) -> dict[str, str]:
    try:
        origin = use_case.architecture_origin
    except ObjectDoesNotExist:
        return {}
    process = origin.process_analysis
    option = origin.solution_option
    return {
        "in_scope": (
            f"Value Stream: {origin.stage.value_stream.name}\n"
            f"Phase: {origin.stage.name}\n"
            + (
                f"Prozess: {process.name}\nStart: {process.scope_start}\nEnde: {process.scope_end}"
                if process
                else origin.stage.description
            )
        ),
        "users_and_scenarios": process.roles if process else origin.stage.actors,
        "solution_outline": option.description if option else use_case.intended_purpose,
        "system_context": process.systems if process else origin.stage.systems,
        "data_context": (
            option.data_requirements
            if option and option.data_requirements
            else process.data_objects
            if process
            else origin.stage.documents
        ),
        "integrations": option.integration_impact if option else "",
        "dependencies": process.handoffs if process else "",
        "risks": option.risks if option else "",
        "assumptions": process.exceptions if process else "",
        "architecture_decisions": (
            option.architecture_fit if option else origin.stage.value_stream.constraints
        ),
    }


def build_initial_delivery_data(use_case: UseCase, decision: ApprovalDecision) -> dict[str, str]:
    metric = (
        f"{use_case.metric_name}: Baseline {use_case.metric_baseline} "
        f"→ Ziel {use_case.metric_target} {use_case.metric_unit}.\n"
        f"Messmethode: {use_case.metric_measurement_method}"
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
    data = {
        "problem_context": (
            f"Problem: {use_case.problem_statement}\n"
            f"Betroffener Prozess: {use_case.affected_process}\n"
            f"Organisationseinheit: {use_case.business_unit}"
        ),
        "target_outcome": use_case.expected_benefit,
        "in_scope": use_case.summary or use_case.affected_process,
        "out_of_scope": "Nicht im MVP enthaltene Funktionen explizit ergänzen.",
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
        "security_privacy_requirements": "\n".join(checks) or "Keine zusätzlichen Prüfungen markiert.",
        "human_oversight": use_case.human_oversight or "Menschliche Kontrolle konkretisieren.",
        "logging_and_audit": "Fachliche Entscheidungen, Fehler und relevante Änderungen protokollieren.",
        "operations_and_support": use_case.support_responsibility or "Betriebsverantwortung festlegen.",
        "mvp_scope": "Kleinsten Ende-zu-Ende-Ablauf für die Nutzenvalidierung beschreiben.",
        "acceptance_criteria": (
            "1. Fachlicher Kernablauf ist Ende-zu-Ende demonstrierbar.\n"
            "2. Freigabeauflagen und Governance-Anforderungen sind umgesetzt.\n"
            f"3. {metric}"
        ),
        "test_scenarios": "Happy Path, Datenfehler, fachliche Ausnahme und manuellen Eingriff testen.",
        "measurement_plan": metric,
        "dependencies": "",
        "risks": "",
        "assumptions": "Offene Annahmen aus Discovery und Bewertung ergänzen.",
        "architecture_decisions": "",
        "initial_backlog": (
            "Epic 1: Kernprozess und Nutzerfluss\n"
            "Epic 2: Daten und Integrationen\n"
            "Epic 3: Governance, Betrieb und Erfolgsmessung"
        ),
        "handover_notes": (
            f"Freigabe: {decision.get_decision_status_display()}\n"
            f"Begründung: {decision.rationale}\n"
            + (f"Auflagen: {decision.conditions}" if decision.conditions else "Keine Auflagen.")
        ),
    }
    for key, value in _architecture_context(use_case).items():
        if value:
            data[key] = value
    return data


@transaction.atomic
def create_delivery_package(*, use_case: UseCase, actor) -> DeliveryPackage:
    eligible, reason, decision = delivery_eligibility(use_case)
    if not eligible or decision is None:
        raise ValidationError(reason)
    version = (
        use_case.delivery_packages.aggregate(max_version=Max("version"))["max_version"] or 0
    ) + 1
    return DeliveryPackage.objects.create(
        use_case=use_case,
        version=version,
        generated_from_decision=decision,
        created_by=actor,
        **build_initial_delivery_data(use_case, decision),
    )


def missing_ready_fields(package: DeliveryPackage) -> list[str]:
    field_labels = {field.name: str(field.verbose_name) for field in package._meta.fields}
    return [
        field_labels[name]
        for name in READY_REQUIRED_FIELDS
        if not str(getattr(package, name, "")).strip()
    ]


def mark_package_ready(package: DeliveryPackage) -> None:
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        raise ValidationError("Ein übergebenes Delivery Package ist unveränderlich.")
    missing = missing_ready_fields(package)
    if missing:
        raise ValidationError("Für die Übergabe fehlen: " + ", ".join(missing))
    package.status = DeliveryPackage.Status.READY
    package.save(update_fields=["status", "updated_at"])


def hand_over_package(package: DeliveryPackage, actor) -> None:
    if package.status != DeliveryPackage.Status.READY:
        raise ValidationError("Nur ein als bereit markiertes Delivery Package kann übergeben werden.")
    package.status = DeliveryPackage.Status.HANDED_OVER
    package.handed_over_by = actor
    package.handed_over_at = timezone.now()
    package.save(
        update_fields=["status", "handed_over_by", "handed_over_at", "updated_at"]
    )


def render_delivery_markdown(package: DeliveryPackage) -> str:
    sections = [
        ("Problem und Geschäftskontext", package.problem_context),
        ("Ziel und Ergebnis", package.target_outcome),
        ("Scope", f"### Im Scope\n{package.in_scope}\n\n### Nicht im Scope\n{package.out_of_scope}"),
        ("Nutzer und Szenarien", package.users_and_scenarios),
        ("Lösungsrahmen", package.solution_outline),
        ("Systemkontext", package.system_context),
        ("Datenkontext", package.data_context),
        ("Integrationen", package.integrations),
        ("Funktionale Anforderungen", package.functional_requirements),
        ("Nichtfunktionale Anforderungen", package.non_functional_requirements),
        ("Security, Datenschutz und Recht", package.security_privacy_requirements),
        ("Menschliche Aufsicht", package.human_oversight),
        ("Logging und Audit", package.logging_and_audit),
        ("Betrieb und Support", package.operations_and_support),
        ("MVP-Scope", package.mvp_scope),
        ("Akzeptanzkriterien", package.acceptance_criteria),
        ("Testfälle", package.test_scenarios),
        ("Erfolgsmessung", package.measurement_plan),
        ("Abhängigkeiten", package.dependencies),
        ("Risiken", package.risks),
        ("Annahmen", package.assumptions),
        ("Architekturentscheidungen", package.architecture_decisions),
        ("Initiales Backlog", package.initial_backlog),
        ("Übergabehinweise", package.handover_notes),
    ]
    body = "\n\n".join(f"## {title}\n\n{content or '–'}" for title, content in sections)
    return (
        f"# Delivery Package – {package.use_case.short_id} {package.use_case.title}\n\n"
        f"Version: {package.version}  \nStatus: {package.get_status_display()}\n\n{body}\n"
    )
