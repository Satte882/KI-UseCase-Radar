from __future__ import annotations

import re
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


@dataclass(frozen=True)
class DeliveryStatusSnapshot:
    code: str
    label: str
    handover_complete: bool


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

_PERCENT_THRESHOLD_RE = re.compile(
    r"(?:[<>]=?|≤|≥|mindestens|maximal|unter|über)?\s*\d+(?:[.,]\d+)?\s*(?:%|prozent)",
    re.IGNORECASE,
)
_SAMPLE_CONTEXT_RE = re.compile(
    r"(?:stichprob|population|testset|evaluationsset|goldstandard|"
    r"\b\d+\s*(?:fälle|vorgänge|beispiele|dokumente|ausgaben|outputs|positive))",
    re.IGNORECASE,
)
_UNCERTAINTY_CONTEXT_RE = re.compile(
    r"(?:konfidenzintervall|fehlerspanne|statistische unsicherheit|aussagekraft)",
    re.IGNORECASE,
)
_CRITICAL_CLASS_RE = re.compile(
    r"(?:seltene?|kritische?|fehlerklass|gezielte?s? testset|edge cases?|randfälle)",
    re.IGNORECASE,
)
_NUMERIC_CONFIDENCE_RE = re.compile(
    r"(?:confidence|konfidenz)(?:\s*score)?\s*(?::|=|>|<|von)?\s*\d+(?:[.,]\d+)?\s*%?",
    re.IGNORECASE,
)
_GENERATIVE_OUTPUT_RE = re.compile(
    r"(?:generativ|freitext|textentwurf|kommunikationsentwurf|llm-ausgabe|antwortentwurf)",
    re.IGNORECASE,
)
_CONFIDENCE_JUSTIFICATION_RE = re.compile(
    r"(?:kalibrier|dokumentierte? semantik|fachlich definiert)",
    re.IGNORECASE,
)
_CONFIDENCE_NEGATION_RE = re.compile(
    r"(?:kein(?:e|en|er|es)?|nicht)\s+(?:pseudo-präzise[nr]?\s+)?(?:numerische[nr]?\s+)?"
    r"(?:confidence|konfidenz)",
    re.IGNORECASE,
)
_LATENCY_BUDGET_RE = re.compile(
    r"(?:p95|ende-zu-ende|e2e|nutzer(?:seitig)?(?:es)?\s+(?:latenz|budget))"
    r"[^\d]{0,30}(?:<|≤|max(?:imal)?\.?|unter)?\s*(\d+(?:[.,]\d+)?)\s*(ms|sekunden?|s\b)",
    re.IGNORECASE,
)
_TIMEOUT_RE = re.compile(
    r"(?:request-|provider-|komponenten-)?timeout[^\d]{0,20}(\d+(?:[.,]\d+)?)\s*(ms|sekunden?|s\b)",
    re.IGNORECASE,
)
_SYNC_RETRY_RE = re.compile(
    r"(?:\bsynchron\w*[^.\n]{0,40}retr(?:y|ies)|retr(?:y|ies)[^.\n]{0,40}\bsynchron\w*)",
    re.IGNORECASE,
)
_RETENTION_RE = re.compile(r"(?:retention|aufbewahr|löschfrist|speicherdauer)", re.IGNORECASE)


def _seconds(match: re.Match[str]) -> float:
    value = float(match.group(1).replace(",", "."))
    return value / 1000 if match.group(2).casefold() == "ms" else value


def _quality_semantic_findings(package: DeliveryPackage) -> list[ReadinessFinding]:
    findings: list[ReadinessFinding] = []
    evaluation_text = "\n".join(
        _text(value)
        for value in (
            package.acceptance_criteria,
            package.test_scenarios,
            package.measurement_plan,
        )
    )
    if _PERCENT_THRESHOLD_RE.search(evaluation_text):
        if not _SAMPLE_CONTEXT_RE.search(evaluation_text):
            findings.append(
                ReadinessFinding(
                    "acceptance_and_measurement",
                    "EVALUATION_POPULATION_MISSING",
                    "warning",
                    (
                        "Prozentuale Qualitätsgrenzen benötigen eine benannte Testpopulation "
                        "und eine nachvollziehbare Stichprobengröße."
                    ),
                )
            )
        elif not _UNCERTAINTY_CONTEXT_RE.search(evaluation_text):
            findings.append(
                ReadinessFinding(
                    "acceptance_and_measurement",
                    "EVALUATION_UNCERTAINTY_UNDOCUMENTED",
                    "warning",
                    (
                        "Für die prozentualen Qualitätsgrenzen ist die statistische "
                        "Aussagekraft beziehungsweise Unsicherheit noch nicht dokumentiert."
                    ),
                )
            )
        if not _CRITICAL_CLASS_RE.search(evaluation_text):
            findings.append(
                ReadinessFinding(
                    "acceptance_and_measurement",
                    "CRITICAL_ERROR_CLASSES_UNDOCUMENTED",
                    "warning",
                    (
                        "Seltene oder kritische Fehlerklassen sollten mit gezielten "
                        "Testfällen beziehungsweise Testsets abgedeckt werden."
                    ),
                )
            )

    confidence_text = "\n".join(
        _text(value)
        for value in (
            package.acceptance_criteria,
            package.human_oversight,
            package.non_functional_requirements,
        )
    )
    unjustified_generative_confidence = any(
        _GENERATIVE_OUTPUT_RE.search(statement)
        and _NUMERIC_CONFIDENCE_RE.search(statement)
        and not _CONFIDENCE_JUSTIFICATION_RE.search(statement)
        and not _CONFIDENCE_NEGATION_RE.search(statement)
        for statement in re.split(r"[\n.!?]+", confidence_text)
    )
    if unjustified_generative_confidence:
        findings.append(
            ReadinessFinding(
                "requirements_and_governance",
                "GENERATIVE_NUMERIC_CONFIDENCE_UNJUSTIFIED",
                "blocker",
                (
                    "Für generative Texte wird ein numerischer Confidence Score verlangt, "
                    "ohne eine belastbare, kalibrierte Semantik zu dokumentieren."
                ),
            )
        )

    artifacts = get_delivery_architecture_artifacts(package)
    latency_text = "\n".join(
        _text(value)
        for value in (
            package.non_functional_requirements,
            package.operations_and_support,
            getattr(artifacts, "integration_operations", ""),
        )
    )
    budget_match = _LATENCY_BUDGET_RE.search(latency_text)
    timeout_match = _TIMEOUT_RE.search(latency_text)
    has_sync_retry = bool(_SYNC_RETRY_RE.search(latency_text))
    if (
        budget_match
        and timeout_match
        and has_sync_retry
        and _seconds(timeout_match) >= _seconds(budget_match)
    ):
        findings.append(
            ReadinessFinding(
                "requirements_and_governance",
                "LATENCY_RETRY_BUDGET_CONFLICT",
                "blocker",
                (
                    "Der Timeout eines einzelnen Versuchs verbraucht bereits das gesamte "
                    "nutzerseitige Ende-zu-Ende-Latenzbudget, obwohl synchrone Retries "
                    "vorgesehen sind."
                ),
            )
        )

    retention_text = "\n".join(
        _text(value)
        for value in (
            package.logging_and_audit,
            package.security_privacy_requirements,
            package.operations_and_support,
        )
    )
    if _RETENTION_RE.search(retention_text):
        required_semantics = {
            "Audit-/Traceability-Metadaten": r"(?:audit|traceability)[-/ ]*metadaten|metadaten",
            "Prompt-/Input-Rohinhalte": r"(?:prompt|input)[-/ ]*(?:roh)?inhalt|rohinhalt",
            "Dokumentinhalte": r"dokumentinhalt",
            "personenbezogene oder besonders schutzbedürftige Daten": (
                r"personenbezogen|schutzbedürftig"
            ),
            "technische Logs/Betriebsdaten": r"technische logs?|betriebsdaten",
            "Zweckbindung und Löschung": r"zweckbind|lösch",
        }
        missing = [
            label
            for label, pattern in required_semantics.items()
            if not re.search(pattern, retention_text, re.IGNORECASE)
        ]
        if missing:
            findings.append(
                ReadinessFinding(
                    "requirements_and_governance",
                    "RETENTION_SEMANTICS_INCOMPLETE",
                    "blocker",
                    (
                        "Die Aufbewahrungsregel unterscheidet noch nicht vollständig: "
                        + ", ".join(missing)
                        + "."
                    ),
                )
            )
    return findings


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
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        # The handed-over version is an immutable snapshot. Later source changes belong to a
        # new package version and must not retroactively invalidate the completed handover.
        return []
    review = reviews_by_key.get("problem_and_target")
    if review is None or not review.source_manifest:
        return []

    try:
        origin = package.use_case.architecture_origin
    except ObjectDoesNotExist:
        origin = None
    objects = {
        "use_case": package.use_case,
        "value_stream": origin.stage.value_stream if origin is not None else None,
        "value_stream_stage": origin.stage if origin is not None else None,
        "process_analysis": origin.process_analysis if origin is not None else None,
        "solution_option": origin.solution_option if origin is not None else None,
    }
    findings: list[ReadinessFinding] = []
    role_source = (review.source_manifest.get("role_sources") or {}).get("technical_owner")
    if role_source is not None:
        snapshot_id = str(role_source.get("id") or "")
        current_id = str(package.use_case.technical_owner_id or "")
        if snapshot_id != current_id:
            findings.append(
                ReadinessFinding(
                    "architecture_and_data",
                    "TECHNICAL_OWNER_SOURCE_CHANGE_UNRESOLVED",
                    "blocker",
                    (
                        "Der Technical Owner wurde am Use Case geändert. Alter Package-Wert, "
                        "neuer Quellwert und Übernahmeentscheidung müssen vor der Übergabe "
                        "nachvollziehbar geklärt werden."
                    ),
                )
            )
    for package_field, source in (review.source_manifest.get("field_sources") or {}).items():
        obj = objects.get(source.get("kind"))
        source_field = source.get("field")
        if obj is None or not source_field:
            continue
        current = getattr(obj, source_field, None)
        current_text = "" if current is None else str(current)
        snapshot_text = str(source.get("value") or "")
        if current_text == snapshot_text:
            continue
        label = str(package._meta.get_field(package_field).verbose_name)
        findings.append(
            ReadinessFinding(
                "delivery_control",
                "SOURCE_CHANGED_AFTER_SNAPSHOT",
                "warning",
                (
                    f"Quelle für „{label}“ geändert: "
                    f"„{snapshot_text or '-'}“ → „{current_text or '-'}“."
                ),
            )
        )
    return findings


def evaluate_delivery_readiness(package: DeliveryPackage) -> list[ReadinessFinding]:
    if package.readiness_schema_version < 2:
        return []

    findings: list[ReadinessFinding] = []
    if package.technical_owner_id is None:
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
        elif review.has_role_collapse:
            findings.append(
                ReadinessFinding(
                    section_key,
                    "INDEPENDENT_CONFIRMATION_MISSING",
                    "blocker",
                    (
                        f"Für „{section_label}“ wurden fachliche und technische "
                        "Bestätigung durch dieselbe Person erteilt. Vor der Übergabe "
                        "ist eine unabhängige Bestätigung durch eine zweite Person "
                        "erforderlich."
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
    findings.extend(_quality_semantic_findings(package))
    return findings


def blocking_findings(package: DeliveryPackage) -> list[ReadinessFinding]:
    return [
        finding for finding in evaluate_delivery_readiness(package) if finding.severity == "blocker"
    ]


def delivery_status_snapshot(package: DeliveryPackage) -> DeliveryStatusSnapshot:
    if package.status == DeliveryPackage.Status.HANDED_OVER:
        if package.handed_over_at is None or blocking_findings(package):
            return DeliveryStatusSnapshot(
                code="handover_inconsistent",
                label="Übergabe blockiert (inkonsistenter Bestand)",
                handover_complete=False,
            )
        return DeliveryStatusSnapshot(
            code=package.status,
            label=package.get_status_display(),
            handover_complete=package.handed_over_at is not None,
        )
    return DeliveryStatusSnapshot(
        code=package.status,
        label=package.get_status_display(),
        handover_complete=False,
    )


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
