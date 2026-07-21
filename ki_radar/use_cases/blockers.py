from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse

from .models import UseCase


@dataclass(frozen=True)
class BlockerDetail:
    code: str
    label: str
    category: str
    action_label: str
    target_url: str
    target_anchor: str = ""
    field_name: str = ""

    @property
    def target_href(self) -> str:
        return f"{self.target_url}{self.target_anchor}"


FIELD_TARGETS = {
    "Titel": "title",
    "Problemstellung": "problem_statement",
    "Organisationseinheit": "business_unit",
    "Betroffener Prozess": "affected_process",
    "Fachlich verantwortliche Person": "business_owner",
    "Erwarteter Nutzen": "expected_benefit",
    "Primäre Erfolgsmetrik": "metric_name",
    "Metriktyp": "metric_type",
    "Optimierungsrichtung": "metric_direction",
    "Einheit": "metric_unit",
    "Baseline-Wert": "metric_baseline",
    "Zielwert": "metric_target",
    "Messmethode": "metric_measurement_method",
    "Datenquellen": "data_sources",
    "Nächster Entscheidungstermin": "next_review_date",
    "Geplantes Pilotende": "planned_pilot_end",
    "Technischer Owner": "technical_owner",
    "Einmalige Kosten": "one_time_cost",
    "Laufende Kosten": "recurring_cost",
    "Support-Verantwortung": "support_responsibility",
    "Menschliche Aufsicht": "human_oversight",
    "Umgang mit Daten und Zugängen": "data_and_access_handling",
    "Beendigungsgrund": "ending_reason",
    "Datenschutzprüfung": "privacy_review_completed",
    "Informationssicherheitsprüfung": "security_review_completed",
    "Rechtsprüfung": "legal_review_completed",
}

ASSESSMENT_BLOCKERS = {
    "Aktuelle strukturierte Bewertung",
    "Confidence ist für eine Freigabe zu niedrig",
    "Technische Machbarkeit ist zu niedrig",
    "Datenverfügbarkeit und -qualität sind zu niedrig",
    "Risiko und Komplexität sind für eine Freigabe zu hoch",
    "Governance-Vorprüfung",
}

DECISION_BLOCKERS = {
    "Positive Freigabeentscheidung",
    "Separate Governance-Bestätigung durch die entscheidende Person",
    "Bewertende und entscheidende Person müssen verschieden sein",
    "Fachlich verantwortliche und freigebende Person müssen verschieden sein",
}


def _code(label: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in label).strip(
        "_"
    )


def build_blocker_details(use_case: UseCase, blockers: list[str]) -> list[BlockerDetail]:
    """Derive actionable metadata from the canonical string blockers.

    The string list remains the compatibility surface. Details are generated from it in one
    place, so UI metadata cannot drift from the server-side gate result.
    """

    edit_url = reverse("use_cases:edit", kwargs={"pk": use_case.pk})
    detail_url = use_case.get_absolute_url()
    has_assessment = use_case.decision_assessments.exists()
    details: list[BlockerDetail] = []

    for label in blockers:
        field_name = FIELD_TARGETS.get(label)
        if field_name:
            details.append(
                BlockerDetail(
                    code=f"missing_{field_name}",
                    label=label,
                    category="data",
                    action_label=f"{label} ergänzen",
                    target_url=f"{edit_url}?highlight={field_name}",
                    target_anchor=f"#field-{field_name}",
                    field_name=field_name,
                )
            )
            continue

        if label == "Governance-Screening":
            details.append(
                BlockerDetail(
                    code="governance_screening_missing",
                    label=label,
                    category="process",
                    action_label="Governance-Screening anlegen",
                    target_url=reverse("governance:create", kwargs={"use_case_id": use_case.pk}),
                )
            )
            continue

        if label in ASSESSMENT_BLOCKERS:
            details.append(
                BlockerDetail(
                    code=_code(label),
                    label=label,
                    category="process",
                    action_label="Bewertung öffnen",
                    target_url=reverse("use_cases:assessment_create", kwargs={"pk": use_case.pk}),
                )
            )
            continue

        if label in DECISION_BLOCKERS:
            target_url = (
                reverse("use_cases:approval_decision_create", kwargs={"pk": use_case.pk})
                if has_assessment
                else reverse("use_cases:assessment_create", kwargs={"pk": use_case.pk})
            )
            action_label = "Freigabeentscheidung öffnen" if has_assessment else "Bewertung anlegen"
            details.append(
                BlockerDetail(
                    code=_code(label),
                    label=label,
                    category="process",
                    action_label=action_label,
                    target_url=target_url,
                )
            )
            continue

        details.append(
            BlockerDetail(
                code=_code(label),
                label=label,
                category="process",
                action_label="Use Case öffnen",
                target_url=detail_url,
            )
        )

    return details
