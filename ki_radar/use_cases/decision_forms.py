from django import forms
from django.contrib.auth import get_user_model

from .models import ApprovalDecision, DecisionAssessment, UseCase


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class DecisionAssessmentForm(forms.ModelForm):
    class Meta:
        model = DecisionAssessment
        fields = [
            "assessment_date",
            "business_value",
            "strategic_fit",
            "technical_feasibility",
            "data_readiness",
            "risk_complexity",
            "evidence_quality",
            "evidence_recency",
            "evidence_coverage",
            "independent_review",
            "assumptions_resolved",
            "evidence_url",
            "rationale",
            "governance_precheck_completed",
            "recommendation",
        ]
        widgets = {
            "assessment_date": DateInput(),
            "rationale": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "assessment_date": "Bewertungsdatum",
            "business_value": "Wirtschaftlicher Nutzen",
            "strategic_fit": "Strategischer Beitrag",
            "technical_feasibility": "Technische Machbarkeit",
            "data_readiness": "Datenverfügbarkeit und -qualität",
            "risk_complexity": "Risiko und Komplexität",
            "evidence_quality": "Qualität der Evidenz",
            "evidence_recency": "Aktualität der Evidenz",
            "evidence_coverage": "Abdeckung der Evidenz",
            "independent_review": "Unabhängige Prüfung",
            "assumptions_resolved": "Klärung offener Annahmen",
            "evidence_url": "Nachweislink",
            "rationale": "Bewertungsbegründung",
            "governance_precheck_completed": "Governance-Vorprüfung durchgeführt",
            "recommendation": "Empfohlene Entscheidung",
        }
        help_texts = {
            "evidence_url": "Verbindlicher Link auf Analyse, Messung oder freigegebenen Nachweis.",
            "governance_precheck_completed": (
                "Falls keine eigene Governance-Rolle existiert, führt die bewertende Person die "
                "Vorprüfung durch. Die entscheidende Person muss sie separat bestätigen."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        for name in [
            "business_value",
            "strategic_fit",
            "technical_feasibility",
            "data_readiness",
            "risk_complexity",
            "evidence_quality",
            "evidence_recency",
            "evidence_coverage",
            "independent_review",
            "assumptions_resolved",
            "recommendation",
        ]:
            self.fields[name].widget.attrs["class"] = "form-select"
        self.fields["governance_precheck_completed"].widget.attrs["class"] = "form-check-input"


class ApprovalDecisionForm(forms.ModelForm):
    class Meta:
        model = ApprovalDecision
        fields = [
            "decision_status",
            "rationale",
            "governance_confirmed",
            "conditions",
            "condition_owner",
            "condition_due_date",
        ]
        widgets = {
            "rationale": forms.Textarea(attrs={"rows": 5}),
            "conditions": forms.Textarea(attrs={"rows": 4}),
            "condition_due_date": DateInput(),
        }
        labels = {
            "decision_status": "Entscheidung",
            "rationale": "Entscheidungsbegründung",
            "governance_confirmed": "Governance-Vorprüfung separat bestätigt",
            "conditions": "Auflagen",
            "condition_owner": "Verantwortliche Person für die Auflage",
            "condition_due_date": "Fälligkeit der Auflage",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["decision_status"].choices = [
            (UseCase.DecisionStatus.DEFERRED, UseCase.DecisionStatus.DEFERRED.label),
            (UseCase.DecisionStatus.APPROVED, UseCase.DecisionStatus.APPROVED.label),
            (
                UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS,
                UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS.label,
            ),
            (UseCase.DecisionStatus.NOT_PURSUED, UseCase.DecisionStatus.NOT_PURSUED.label),
        ]
        users = get_user_model().objects.filter(is_active=True, is_anonymized=False).order_by(
            "last_name", "first_name", "username"
        )
        self.fields["condition_owner"].queryset = users
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["decision_status"].widget.attrs["class"] = "form-select"
        self.fields["condition_owner"].widget.attrs["class"] = "form-select"
        self.fields["governance_confirmed"].widget.attrs["class"] = "form-check-input"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision_status") == UseCase.DecisionStatus.APPROVED_WITH_CONDITIONS:
            for field_name in ["conditions", "condition_owner", "condition_due_date"]:
                if not cleaned.get(field_name):
                    self.add_error(
                        field_name,
                        "Dieses Feld ist für eine Freigabe mit Auflagen erforderlich.",
                    )
        return cleaned
