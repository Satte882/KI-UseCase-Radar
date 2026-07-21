from __future__ import annotations

from django.utils import timezone

from ki_radar.architecture.models import (
    ProcessAnalysis,
    SolutionOption,
    UseCaseOrigin,
    ValueStream,
    ValueStreamStage,
)
from ki_radar.delivery.models import DeliveryPackage
from ki_radar.delivery.services import build_initial_delivery_data
from ki_radar.use_cases.models import ApprovalDecision, DecisionAssessment, UseCase

DEMO_VALUE_STREAM_NAME = "[DEMO] Beschaffung bis Zahlung"
DEMO_USE_CASE_TITLE = "[DEMO] Automatische Rechnungspruefung"


def seed_demo_architecture_data() -> dict[str, int]:
    use_case = UseCase.objects.select_related("business_unit").get(title=DEMO_USE_CASE_TITLE)
    owner = use_case.business_owner
    coordinator = use_case.coordinator
    if owner is None or coordinator is None:
        return {
            "value_streams": 0,
            "process_analyses": 0,
            "solution_options": 0,
            "delivery_packages": 0,
        }

    value_stream, _ = ValueStream.objects.update_or_create(
        name=DEMO_VALUE_STREAM_NAME,
        defaults={
            "description": "End-to-End-Wertschöpfung vom Bedarf bis zur bezahlten Leistung.",
            "business_unit": use_case.business_unit,
            "owner": owner,
            "created_by": coordinator,
            "trigger": "Ein fachlich freigegebener Bedarf liegt vor.",
            "outcome": "Die Leistung ist geprüft, verbucht und bezahlt.",
            "scope": "Bedarf, Beschaffung, Leistungserbringung und Zahlung.",
            "strategic_objective": (
                "Durchlaufzeit senken und Entscheidungen nachvollziehbar machen."
            ),
            "stakeholders": "Fachbereich, Einkauf, Lieferanten, Buchhaltung und IT.",
            "constraints": (
                "Das ERP bleibt führend; Entscheidungen werden nicht vollautomatisiert."
            ),
            "status": ValueStream.Status.ACTIVE,
        },
    )
    stage, _ = ValueStreamStage.objects.update_or_create(
        value_stream=value_stream,
        sequence=5,
        defaults={
            "name": "Eingangsrechnung prüfen",
            "description": "Rechnung mit Bestellung und Wareneingang abgleichen.",
            "actors": "Einkauf, Buchhaltung und fachliche Freigabe.",
            "systems": "ERP und Dokumentenmanagement.",
            "documents": "Rechnung, Bestellung und Wareneingang.",
            "pain_points": (
                "Manuelle Prüfung dauert lange; Abweichungen werden uneinheitlich bewertet."
            ),
            "baseline_metrics": "Rund elf Minuten Prüfzeit je Rechnung.",
        },
    )
    process, _ = ProcessAnalysis.objects.update_or_create(
        stage=stage,
        name="Eingangsrechnungsprüfung",
        defaults={
            "status": ProcessAnalysis.Status.TARGET_DEFINED,
            "scope_start": "Eine Rechnung ist eingegangen.",
            "scope_end": ("Die Rechnung ist freigegeben oder zur Klärung zurückgegeben."),
            "trigger": "Eingang einer neuen Rechnung.",
            "outcome": "Nachvollziehbare Zahlungsfreigabe oder begründete Abweichung.",
            "current_flow": (
                "Rechnung öffnen, Bestell- und Wareneingangsdaten suchen, Positionen "
                "vergleichen, Abweichungen bewerten und Freigabe dokumentieren."
            ),
            "roles": ("Buchhaltung prüft formal; Einkauf und Fachbereich klären Abweichungen."),
            "systems": "ERP, Dokumentenmanagement und E-Mail.",
            "data_objects": ("Rechnung, Bestellung, Wareneingang und Lieferantenstammdaten."),
            "business_rules": ("Betrag, Menge, Preis und Bestellbezug müssen plausibel sein."),
            "handoffs": ("Buchhaltung übergibt Abweichungen an Einkauf oder Fachbereich."),
            "bottlenecks": ("Manuelle Suche, Medienbrüche und Rückfragen verursachen Wartezeit."),
            "exceptions": (
                "Teilrechnungen, fehlende Bestellnummern und abweichende Mengeneinheiten."
            ),
            "baseline_metrics": ("Elf Minuten je Rechnung; mehrere Rückfragen pro Woche."),
            "target_state_principles": (
                "Standardfälle automatisiert vorbereiten, Abweichungen erklären und die "
                "fachliche Freigabe beim Menschen belassen."
            ),
            "analyzed_by": coordinator,
        },
    )
    option, _ = SolutionOption.objects.update_or_create(
        process_analysis=process,
        name="Regel- und KI-gestützte Rechnungsprüfung",
        defaults={
            "option_type": SolutionOption.OptionType.ASSISTANT,
            "recommendation": SolutionOption.Recommendation.PREFERRED,
            "description": (
                "Rechnungsdaten extrahieren, regelbasiert abgleichen und nicht eindeutige "
                "Abweichungen zur fachlichen Prüfung markieren."
            ),
            "expected_value": ("Prüfzeit reduzieren und Abweichungen konsistenter behandeln."),
            "feasibility": "medium",
            "data_requirements": "Rechnungen, Bestellungen und Wareneingangsdaten.",
            "application_impact": "Erweiterung der internen Rechnungsprüfung.",
            "integration_impact": "ERP- und Dokumentenmanagement-Schnittstelle.",
            "technology_constraints": ("Interne Verarbeitung und nachvollziehbare Regeln."),
            "risks": ("Sonderfälle dürfen nicht fälschlich automatisch freigegeben werden."),
            "architecture_fit": (
                "Standardfälle werden vorbereitet; das ERP bleibt führend und der Mensch "
                "entscheidet über Abweichungen."
            ),
            "created_by": coordinator,
        },
    )
    UseCaseOrigin.objects.update_or_create(
        use_case=use_case,
        defaults={
            "stage": stage,
            "process_analysis": process,
            "solution_option": option,
        },
    )

    assessment, _ = DecisionAssessment.objects.update_or_create(
        use_case=use_case,
        version=1,
        defaults={
            "assessment_date": timezone.localdate(),
            "assessed_by": coordinator,
            "business_value": UseCase.Level.HIGH,
            "strategic_fit": UseCase.Level.HIGH,
            "technical_feasibility": UseCase.Level.MEDIUM,
            "data_readiness": UseCase.Level.MEDIUM,
            "risk_complexity": UseCase.Level.MEDIUM,
            "evidence_quality": DecisionAssessment.EvidenceQuality.REPRESENTATIVE,
            "evidence_recency": DecisionAssessment.ConfidenceFactor.SOLID,
            "evidence_coverage": DecisionAssessment.ConfidenceFactor.SOLID,
            "independent_review": DecisionAssessment.ConfidenceFactor.SOLID,
            "assumptions_resolved": DecisionAssessment.ConfidenceFactor.SOLID,
            "evidence_url": ("https://example.invalid/evidence/demo-rechnungspruefung-delivery"),
            "rationale": (
                "Prozessmessung, Datenstichprobe und technischer Lösungsrahmen liegen vor."
            ),
            "governance_precheck_completed": True,
            "recommendation": UseCase.DecisionStatus.APPROVED,
        },
    )
    decision = ApprovalDecision.objects.filter(
        use_case=use_case,
        assessment=assessment,
    ).first()
    if decision is None:
        decision = ApprovalDecision.objects.create(
            use_case=use_case,
            assessment=assessment,
            decision_status=UseCase.DecisionStatus.APPROVED,
            rationale=("Pilot und Delivery Package sind für den Demo-Use-Case freigegeben."),
            decided_by=coordinator,
            governance_confirmed=True,
            finalized_at=timezone.now(),
        )
    else:
        decision.decision_status = UseCase.DecisionStatus.APPROVED
        decision.rationale = "Pilot und Delivery Package sind für den Demo-Use-Case freigegeben."
        decision.decided_by = coordinator
        decision.governance_confirmed = True
        decision.finalized_at = timezone.now()
        decision.save()

    use_case.decision_status = UseCase.DecisionStatus.APPROVED
    use_case.save(update_fields=["decision_status", "updated_at"])

    initial = build_initial_delivery_data(use_case, decision)
    package = DeliveryPackage.objects.filter(use_case=use_case, version=1).first()
    if package is None:
        DeliveryPackage.objects.create(
            use_case=use_case,
            version=1,
            status=DeliveryPackage.Status.READY,
            generated_from_decision=decision,
            created_by=coordinator,
            **initial,
        )
    elif package.status != DeliveryPackage.Status.HANDED_OVER:
        package.status = DeliveryPackage.Status.READY
        package.generated_from_decision = decision
        package.created_by = coordinator
        for field_name, value in initial.items():
            setattr(package, field_name, value)
        package.save()

    return {
        "value_streams": 1,
        "process_analyses": 1,
        "solution_options": 1,
        "delivery_packages": 1,
    }


def clear_demo_architecture_data() -> dict[str, int]:
    origin_count, _ = UseCaseOrigin.objects.filter(
        stage__value_stream__name=DEMO_VALUE_STREAM_NAME
    ).delete()
    stream_count, _ = ValueStream.objects.filter(name=DEMO_VALUE_STREAM_NAME).delete()
    return {
        "architecture_origins": origin_count,
        "value_streams": stream_count,
    }
