from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

from django.utils import timezone

from ki_radar.delivery.services import current_handed_over_package
from ki_radar.governance.models import GovernanceReview

from .models import UseCase

SCALE_READINESS_SCHEMA_VERSION = 1

SCALE_EVIDENCE_FIELDS = (
    "scale_tailoring_level",
    "scale_pilot_validation_confirmed",
    "scale_production_version",
    "scale_rollback_tested",
    "scale_technical_monitoring_ready",
    "scale_ai_quality_monitoring_ready",
    "scale_incident_process_ready",
    "scale_extended_controls_completed",
    "scale_evidence_url",
    "ml_score_data",
    "ml_score_model",
    "ml_score_infrastructure",
    "ml_score_monitoring",
    "ml_score_minimum",
    "ml_score_version",
    "ml_score_date",
    "ml_score_evidence_url",
    "ml_score_open_core_checks",
    "ml_score_failed_mandatory_checks",
)

ML_SCORE_FIELDS = (
    ("ml_score_data", "Data"),
    ("ml_score_model", "Model"),
    ("ml_score_infrastructure", "Infrastructure"),
    ("ml_score_monitoring", "Monitoring"),
)

TAILORING_ORDER = {"A": 1, "B": 2, "C": 3}


@dataclass(frozen=True)
class ScaleReadinessFinding:
    code: str
    dimension: str
    severity: str
    message: str


@dataclass(frozen=True)
class ScaleReadinessDimension:
    key: str
    label: str
    state: str
    findings: tuple[ScaleReadinessFinding, ...]


@dataclass(frozen=True)
class ScaleReadinessResult:
    state: str
    dimensions: tuple[ScaleReadinessDimension, ...]
    findings: tuple[ScaleReadinessFinding, ...]
    final_ml_score: Decimal | None
    tailoring_level: str

    @property
    def blockers(self) -> tuple[ScaleReadinessFinding, ...]:
        return tuple(item for item in self.findings if item.severity == "blocker")

    @property
    def conditions(self) -> tuple[ScaleReadinessFinding, ...]:
        return tuple(item for item in self.findings if item.severity == "condition")

    @property
    def state_label(self) -> str:
        return {
            "ready": "Bereit",
            "conditional": "Bereit mit Auflagen",
            "not_ready": "Nicht bereit",
        }[self.state]


def extract_scale_evidence(data: dict) -> dict:
    return {field_name: data.pop(field_name, None) for field_name in SCALE_EVIDENCE_FIELDS}


def scale_evidence_from_mapping(data: Mapping | None) -> dict:
    if not data:
        return {}
    return {field_name: data.get(field_name) for field_name in SCALE_EVIDENCE_FIELDS}


def _text(value) -> str:
    return str(value or "").strip()


def _bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).casefold() in {"1", "true", "yes", "on"}


def _decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _iso(value) -> str:
    if value is None:
        return ""
    isoformat = getattr(value, "isoformat", None)
    return isoformat() if callable(isoformat) else str(value)


def _display_name(user) -> str:
    if user is None:
        return ""
    display_name = getattr(user, "get_display_name", None)
    return display_name() if callable(display_name) else str(user)


def _minimum_tailoring(use_case: UseCase) -> str:
    assessment = use_case.governance_assessments.first()
    if assessment and any(
        getattr(assessment, field_name)
        for field_name in (
            "personal_data",
            "employee_data",
            "automated_person_assessment",
            "influences_person_decisions",
            "biometric_data",
            "safety_critical",
            "regulated_product",
            "health_safety_rights_impact",
        )
    ):
        return "C"
    return "A"


def _governance_findings(use_case: UseCase) -> list[ScaleReadinessFinding]:
    findings: list[ScaleReadinessFinding] = []
    latest_by_type: dict[str, GovernanceReview] = {}
    for review in use_case.governance_reviews.order_by("-created_at", "-reviewed_at"):
        latest_by_type.setdefault(review.review_type, review)

    for review_type, required, completed, label in (
        (
            GovernanceReview.ReviewType.PRIVACY,
            use_case.privacy_review_required,
            use_case.privacy_review_completed,
            "Datenschutz",
        ),
        (
            GovernanceReview.ReviewType.SECURITY,
            use_case.security_review_required,
            use_case.security_review_completed,
            "Informationssicherheit",
        ),
        (
            GovernanceReview.ReviewType.LEGAL,
            use_case.legal_review_required,
            use_case.legal_review_completed,
            "Recht",
        ),
    ):
        if required and not completed:
            findings.append(
                ScaleReadinessFinding(
                    code=f"GOVERNANCE_{review_type.upper()}_OPEN",
                    dimension="responsibility",
                    severity="blocker",
                    message=f"{label} ist als erforderliche formale Prüfung noch offen.",
                )
            )
            continue
        review = latest_by_type.get(review_type)
        if review is None:
            continue
        if review.status == GovernanceReview.Status.COMPLETED:
            if review.result == GovernanceReview.Result.FAILED:
                findings.append(
                    ScaleReadinessFinding(
                        code=f"GOVERNANCE_{review_type.upper()}_FAILED",
                        dimension="responsibility",
                        severity="blocker",
                        message=f"{label} wurde nicht bestanden.",
                    )
                )
            elif review.result == GovernanceReview.Result.PASSED_WITH_CONDITIONS:
                findings.append(
                    ScaleReadinessFinding(
                        code=f"GOVERNANCE_{review_type.upper()}_CONDITIONAL",
                        dimension="responsibility",
                        severity="condition",
                        message=f"{label} ist nur mit dokumentierten Auflagen freigegeben.",
                    )
                )
    return findings


def evaluate_scale_readiness(use_case: UseCase, evidence: Mapping | None = None) -> ScaleReadinessResult:
    data = scale_evidence_from_mapping(evidence)
    findings: list[ScaleReadinessFinding] = []

    tailoring = _text(data.get("scale_tailoring_level")).upper()
    minimum_tailoring = _minimum_tailoring(use_case)
    if tailoring not in TAILORING_ORDER:
        findings.append(
            ScaleReadinessFinding(
                code="TAILORING_MISSING",
                dimension="responsibility",
                severity="blocker",
                message="Tailoring-Stufe A, B oder C muss für die Scale-Entscheidung festgelegt sein.",
            )
        )
        tailoring = ""
    elif TAILORING_ORDER[tailoring] < TAILORING_ORDER[minimum_tailoring]:
        findings.append(
            ScaleReadinessFinding(
                code="TAILORING_TOO_LOW",
                dimension="responsibility",
                severity="blocker",
                message=(
                    f"Die gewählte Tailoring-Stufe {tailoring} unterschreitet die aus dem "
                    f"Governance-Kontext erforderliche Mindeststufe {minimum_tailoring}."
                ),
            )
        )

    if use_case.metric_result == UseCase.MetricResult.NOT_ACHIEVED:
        findings.append(
            ScaleReadinessFinding(
                code="PILOT_TARGET_NOT_ACHIEVED",
                dimension="pilot",
                severity="condition",
                message="Das definierte Pilotziel wurde nicht erreicht.",
            )
        )
    if not _bool(data.get("scale_pilot_validation_confirmed")):
        findings.append(
            ScaleReadinessFinding(
                code="PILOT_VALIDATION_NOT_CONFIRMED",
                dimension="pilot",
                severity="blocker",
                message=(
                    "Pilotumfang, Repräsentativität sowie relevante Fehler- und Ausnahmefälle "
                    "müssen für den geplanten Produktivscope bestätigt sein."
                ),
            )
        )

    ml_scores: list[Decimal] = []
    score_dimensions = {
        "ml_score_data": "data",
        "ml_score_model": "quality",
        "ml_score_infrastructure": "deployment",
        "ml_score_monitoring": "monitoring",
    }
    for field_name, label in ML_SCORE_FIELDS:
        value = _decimal(data.get(field_name))
        if value is None:
            findings.append(
                ScaleReadinessFinding(
                    code=f"ML_SCORE_{field_name.removeprefix('ml_score_').upper()}_MISSING",
                    dimension=score_dimensions[field_name],
                    severity="blocker",
                    message=f"Der aktuelle ML-Test-Score für {label} fehlt.",
                )
            )
        elif value < Decimal("0") or value > Decimal("7"):
            findings.append(
                ScaleReadinessFinding(
                    code=f"ML_SCORE_{field_name.removeprefix('ml_score_').upper()}_INVALID",
                    dimension=score_dimensions[field_name],
                    severity="blocker",
                    message=f"Der ML-Test-Score für {label} muss zwischen 0 und 7 liegen.",
                )
            )
        else:
            ml_scores.append(value)

    final_ml_score = min(ml_scores) if len(ml_scores) == len(ML_SCORE_FIELDS) else None
    minimum_score = _decimal(data.get("ml_score_minimum"))
    if minimum_score is None:
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_MINIMUM_MISSING",
                dimension="quality",
                severity="blocker",
                message="Der projektspezifische ML-Test-Score-Mindestwert fehlt.",
            )
        )
    elif minimum_score < Decimal("0") or minimum_score > Decimal("7"):
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_MINIMUM_INVALID",
                dimension="quality",
                severity="blocker",
                message="Der projektspezifische ML-Test-Score-Mindestwert muss zwischen 0 und 7 liegen.",
            )
        )
    elif final_ml_score is not None and final_ml_score < minimum_score:
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_BELOW_MINIMUM",
                dimension="quality",
                severity="blocker",
                message=(
                    f"Der ML-Test-Score {final_ml_score} unterschreitet den "
                    f"projektspezifischen Mindestwert {minimum_score}."
                ),
            )
        )

    if not _text(data.get("ml_score_version")):
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_VERSION_MISSING",
                dimension="quality",
                severity="blocker",
                message="Version der aktuellen ML-Test-Score-Erhebung fehlt.",
            )
        )
    if not data.get("ml_score_date"):
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_DATE_MISSING",
                dimension="quality",
                severity="blocker",
                message="Datum der aktuellen ML-Test-Score-Erhebung fehlt.",
            )
        )
    if not _text(data.get("ml_score_evidence_url")):
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_EVIDENCE_MISSING",
                dimension="quality",
                severity="blocker",
                message="Nachweisreferenz der aktuellen ML-Test-Score-Erhebung fehlt.",
            )
        )
    if _text(data.get("ml_score_failed_mandatory_checks")):
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_MANDATORY_CHECK_FAILED",
                dimension="quality",
                severity="blocker",
                message="Mindestens eine zwingende ML-Test-Score-Einzelprüfung ist nicht erfüllt.",
            )
        )
    if _text(data.get("ml_score_open_core_checks")):
        findings.append(
            ScaleReadinessFinding(
                code="ML_SCORE_CORE_CHECKS_OPEN",
                dimension="quality",
                severity="condition",
                message="Im ML-Test-Score bestehen noch dokumentierte offene Kernprüfungen.",
            )
        )

    package = current_handed_over_package(use_case)
    if package is None:
        findings.append(
            ScaleReadinessFinding(
                code="DELIVERY_HANDOVER_MISSING",
                dimension="deployment",
                severity="blocker",
                message="Das aktuelle Delivery Package ist nicht verbindlich übergeben.",
            )
        )
    if not _text(data.get("scale_production_version")):
        findings.append(
            ScaleReadinessFinding(
                code="PRODUCTION_VERSION_MISSING",
                dimension="deployment",
                severity="blocker",
                message="Die freigegebene Produktivversion ist nicht eindeutig identifiziert.",
            )
        )
    if not _bool(data.get("scale_rollback_tested")):
        findings.append(
            ScaleReadinessFinding(
                code="ROLLBACK_NOT_TESTED",
                dimension="deployment",
                severity="blocker",
                message="Rollback oder Deaktivierung wurde nicht praktisch getestet.",
            )
        )

    if not _text(data.get("scale_evidence_url")):
        findings.append(
            ScaleReadinessFinding(
                code="OPERATIONS_EVIDENCE_MISSING",
                dimension="monitoring",
                severity="blocker",
                message="Nachweisreferenz für Release-, Monitoring- und Betriebsfähigkeit fehlt.",
            )
        )
    if not _bool(data.get("scale_technical_monitoring_ready")):
        findings.append(
            ScaleReadinessFinding(
                code="TECHNICAL_MONITORING_MISSING",
                dimension="monitoring",
                severity="blocker",
                message="Technisches Monitoring und Alarmierung sind nicht nachgewiesen.",
            )
        )
    if not _bool(data.get("scale_ai_quality_monitoring_ready")):
        findings.append(
            ScaleReadinessFinding(
                code="AI_QUALITY_MONITORING_MISSING",
                dimension="monitoring",
                severity="blocker",
                message="AI-/fachliches Qualitätsmonitoring ist nicht nachgewiesen.",
            )
        )
    if tailoring in {"B", "C"} and not _bool(data.get("scale_incident_process_ready")):
        findings.append(
            ScaleReadinessFinding(
                code="INCIDENT_PROCESS_MISSING",
                dimension="monitoring",
                severity="blocker",
                message="Incident- und Eskalationsprozess ist für dieses Tailoring nicht nachgewiesen.",
            )
        )

    if use_case.business_owner_id is None:
        findings.append(
            ScaleReadinessFinding(
                code="BUSINESS_OWNER_MISSING",
                dimension="responsibility",
                severity="blocker",
                message="Business Owner fehlt.",
            )
        )
    if use_case.technical_owner_id is None:
        findings.append(
            ScaleReadinessFinding(
                code="TECHNICAL_OWNER_MISSING",
                dimension="responsibility",
                severity="blocker",
                message="Technical Owner fehlt.",
            )
        )
    if not _text(use_case.support_responsibility):
        findings.append(
            ScaleReadinessFinding(
                code="SUPPORT_RESPONSIBILITY_MISSING",
                dimension="responsibility",
                severity="blocker",
                message="Betriebs- und Supportverantwortung ist nicht geklärt.",
            )
        )
    if not _text(use_case.human_oversight):
        findings.append(
            ScaleReadinessFinding(
                code="HUMAN_OVERSIGHT_MISSING",
                dimension="responsibility",
                severity="blocker",
                message="Human Oversight ist nicht geklärt.",
            )
        )

    findings.extend(_governance_findings(use_case))
    if tailoring == "C" and not _bool(data.get("scale_extended_controls_completed")):
        findings.append(
            ScaleReadinessFinding(
                code="EXTENDED_CONTROLS_MISSING",
                dimension="responsibility",
                severity="blocker",
                message=(
                    "Die zusätzlichen Nachweise für Tailoring C "
                    "(z. B. unabhängiges Review, Recovery/Security und Abschaltverfahren) "
                    "sind nicht vollständig bestätigt."
                ),
            )
        )

    dimension_labels = (
        ("pilot", "Pilot-Evidenz / Wirkung"),
        ("data", "Daten & Wissen"),
        ("quality", "AI-/Systemqualität"),
        ("deployment", "Deployment & technische Robustheit"),
        ("monitoring", "Monitoring & Betrieb"),
        ("responsibility", "Verantwortung, Governance & Restrisiko"),
    )
    dimensions: list[ScaleReadinessDimension] = []
    for key, label in dimension_labels:
        dimension_findings = tuple(item for item in findings if item.dimension == key)
        if any(item.severity == "blocker" for item in dimension_findings):
            state = "not_ready"
        elif any(item.severity == "condition" for item in dimension_findings):
            state = "conditional"
        else:
            state = "ready"
        dimensions.append(
            ScaleReadinessDimension(
                key=key,
                label=label,
                state=state,
                findings=dimension_findings,
            )
        )

    if any(item.severity == "blocker" for item in findings):
        state = "not_ready"
    elif any(item.severity == "condition" for item in findings):
        state = "conditional"
    else:
        state = "ready"

    return ScaleReadinessResult(
        state=state,
        dimensions=tuple(dimensions),
        findings=tuple(findings),
        final_ml_score=final_ml_score,
        tailoring_level=tailoring,
    )


def build_scale_readiness_snapshot(
    use_case: UseCase,
    evidence: Mapping | None,
    result: ScaleReadinessResult,
) -> dict:
    data = scale_evidence_from_mapping(evidence)
    package = current_handed_over_package(use_case)
    governance_reviews = [
        {
            "id": review.pk,
            "type": review.review_type,
            "status": review.status,
            "result": review.result,
            "reviewed_at": _iso(review.reviewed_at),
            "evidence_url": review.evidence_url,
        }
        for review in use_case.governance_reviews.order_by("review_type", "-created_at")
    ]
    return {
        "schema_version": SCALE_READINESS_SCHEMA_VERSION,
        "captured_at": timezone.now().isoformat(),
        "state": result.state,
        "tailoring_level": result.tailoring_level,
        "pilot": {
            "use_case_id": str(use_case.pk),
            "pilot_start": _iso(use_case.pilot_start),
            "metric_result": use_case.metric_result,
            "metric_measured_at": _iso(use_case.metric_measured_at),
            "metric_evidence_url": use_case.metric_evidence_url,
            "validation_confirmed": _bool(data.get("scale_pilot_validation_confirmed")),
        },
        "delivery": {
            "package_id": str(package.pk) if package else "",
            "package_version": package.version if package else None,
            "handed_over_at": _iso(package.handed_over_at) if package else "",
            "production_version": _text(data.get("scale_production_version")),
            "operations_evidence_url": _text(data.get("scale_evidence_url")),
        },
        "ml_test_score": {
            "data": str(_decimal(data.get("ml_score_data")) or ""),
            "model": str(_decimal(data.get("ml_score_model")) or ""),
            "infrastructure": str(_decimal(data.get("ml_score_infrastructure")) or ""),
            "monitoring": str(_decimal(data.get("ml_score_monitoring")) or ""),
            "final": str(result.final_ml_score or ""),
            "minimum": str(_decimal(data.get("ml_score_minimum")) or ""),
            "version": _text(data.get("ml_score_version")),
            "date": _iso(data.get("ml_score_date")),
            "evidence_url": _text(data.get("ml_score_evidence_url")),
            "open_core_checks": _text(data.get("ml_score_open_core_checks")),
            "failed_mandatory_checks": _text(data.get("ml_score_failed_mandatory_checks")),
        },
        "operations": {
            "rollback_tested": _bool(data.get("scale_rollback_tested")),
            "technical_monitoring_ready": _bool(data.get("scale_technical_monitoring_ready")),
            "ai_quality_monitoring_ready": _bool(data.get("scale_ai_quality_monitoring_ready")),
            "incident_process_ready": _bool(data.get("scale_incident_process_ready")),
            "extended_controls_completed": _bool(data.get("scale_extended_controls_completed")),
        },
        "governance_reviews": governance_reviews,
        "roles": {
            "business_owner_id": str(use_case.business_owner_id or ""),
            "business_owner": _display_name(use_case.business_owner),
            "technical_owner_id": str(use_case.technical_owner_id or ""),
            "technical_owner": _display_name(use_case.technical_owner),
        },
        "findings": [
            {
                "code": finding.code,
                "dimension": finding.dimension,
                "severity": finding.severity,
                "message": finding.message,
            }
            for finding in result.findings
        ],
    }


_original_apply_status_transition = None


def _apply_status_transition_with_scale_readiness(
    *,
    use_case: UseCase,
    target_status: str,
    actor,
    pilot_start=None,
    allow_early_go_live_exception: bool = False,
    scale_evidence: Mapping | None = None,
):
    if _original_apply_status_transition is None:
        raise RuntimeError("Scale Readiness enforcement is not installed.")

    if target_status == UseCase.Status.OPERATION and use_case.status == UseCase.Status.PILOT:
        result = evaluate_scale_readiness(use_case, scale_evidence)
        if result.blockers:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "Scale Readiness blockiert: "
                + "; ".join(finding.message for finding in result.blockers)
            )

    return _original_apply_status_transition(
        use_case=use_case,
        target_status=target_status,
        actor=actor,
        pilot_start=pilot_start,
        allow_early_go_live_exception=allow_early_go_live_exception,
    )


def install() -> None:
    global _original_apply_status_transition

    from . import services

    if services.apply_status_transition is _apply_status_transition_with_scale_readiness:
        return
    _original_apply_status_transition = services.apply_status_transition
    services.apply_status_transition = _apply_status_transition_with_scale_readiness
