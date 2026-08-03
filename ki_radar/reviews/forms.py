from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.permissions import (
    can_confirm_early_go_live_exception,
    can_confirm_go_live_exception,
)
from ki_radar.use_cases.services import current_decision_check, validate_pilot_start_date

from .models import Review


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class ReviewForm(forms.ModelForm):
    pilot_start = forms.DateField(
        required=False,
        widget=DateInput(),
        label="Tatsächlicher Pilotbeginn",
        help_text=(
            "Heute oder ein früheres Datum ab der verbindlichen Übergabe des aktuellen "
            "Delivery Packages."
        ),
    )
    ending_reason = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Beendigungsgrund"
    )
    data_and_access_handling = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Umgang mit Daten und Zugängen",
    )
    replacement_solution = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Ersatzlösung"
    )
    final_assessment = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Abschlussbewertung"
    )
    lessons_learned = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Lessons Learned"
    )
    go_live_exception_confirmed = forms.BooleanField(
        required=False,
        label="Go-live trotz verfehltem Pilotziel ausdrücklich bestätigen",
        help_text=(
            "Nur erforderlich, wenn die primäre Erfolgsmetrik das definierte Ziel nicht erreicht. "
            "Die Begründung gehört in das Feld Entscheidungsbegründung."
        ),
    )
    early_go_live_exception_confirmed = forms.BooleanField(
        required=False,
        label="Vorzeitige Produktivsetzung ausdrücklich bestätigen",
        help_text=(
            "Nur für eine Produktivsetzung vor dem geplanten Pilotende. Diese Ausnahme ist "
            "getrennt von einer Ausnahme bei verfehltem Pilotziel."
        ),
    )
    early_go_live_original_pilot_end = forms.DateField(
        required=False,
        disabled=True,
        widget=DateInput(),
        label="Ursprüngliches geplantes Pilotende",
    )
    early_go_live_evidence_basis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Bereits vorliegende Mess- und Evidenzbasis",
    )
    early_go_live_unobserved_risks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Noch nicht vollständig beobachtete Risiken",
    )
    early_go_live_mitigation_measures = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Maßnahmen zur Risikobegrenzung",
    )

    class Meta:
        model = Review
        fields = [
            "review_date",
            "pilot_start",
            "decision",
            "new_status",
            "rationale",
            "go_live_exception_confirmed",
            "early_go_live_exception_confirmed",
            "early_go_live_original_pilot_end",
            "early_go_live_evidence_basis",
            "early_go_live_unobserved_risks",
            "early_go_live_mitigation_measures",
            "open_actions",
            "action_owner",
            "action_due_date",
            "next_review_date",
        ]
        widgets = {
            "review_date": DateInput(),
            "action_due_date": DateInput(),
            "next_review_date": DateInput(),
            "rationale": forms.Textarea(attrs={"rows": 4}),
            "open_actions": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "review_date": "Review-Datum",
            "decision": "Entscheidung",
            "new_status": "Neuer Status",
            "rationale": "Entscheidungsbegründung",
            "open_actions": "Offene Maßnahmen",
            "action_owner": "Maßnahmenverantwortliche Person",
            "action_due_date": "Fälligkeitsdatum der Maßnahme",
            "next_review_date": "Nächster Entscheidungstermin",
        }

    def __init__(
        self,
        *args,
        use_case: UseCase,
        actor=None,
        pilot_start_only: bool = False,
        requested_action: str | None = None,
        **kwargs,
    ):
        self.use_case = use_case
        self.actor = actor
        self.pilot_start_only = pilot_start_only
        self.requested_action = requested_action
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["review_date"].initial = today
        self.fields["pilot_start"].initial = use_case.pilot_start or today
        self.fields["pilot_start"].widget.attrs["max"] = today.isoformat()
        self.fields["next_review_date"].initial = use_case.next_review_date
        self.fields["early_go_live_original_pilot_end"].initial = use_case.planned_pilot_end
        if not self.is_bound:
            if requested_action == "go_live" and use_case.status == UseCase.Status.PILOT:
                self.fields["decision"].initial = Review.Decision.GO_LIVE
                self.fields["new_status"].initial = UseCase.Status.OPERATION
            elif requested_action == "closure" and use_case.status != UseCase.Status.ENDED:
                self.fields["decision"].initial = Review.Decision.END
                self.fields["new_status"].initial = UseCase.Status.ENDED
            else:
                decision = current_decision_check(use_case)
                initial_decision = {
                    UseCase.Status.REVIEW: Review.Decision.START_REVIEW,
                    UseCase.Status.PILOT: Review.Decision.START_PILOT,
                    UseCase.Status.OPERATION: (
                        Review.Decision.CONTINUE
                        if use_case.status == UseCase.Status.OPERATION
                        else Review.Decision.GO_LIVE
                    ),
                    UseCase.Status.ENDED: Review.Decision.END,
                }.get(decision.target_status)
                if initial_decision:
                    self.fields["decision"].initial = initial_decision
                self.fields["new_status"].initial = decision.target_status
        if pilot_start_only:
            self.fields["decision"].initial = Review.Decision.START_PILOT
            self.fields["new_status"].initial = UseCase.Status.PILOT
            for name in ["decision", "new_status", "go_live_exception_confirmed"]:
                self.fields[name].disabled = True
                self.fields[name].widget = forms.HiddenInput()
            self.fields["pilot_start"].required = True
            for name in [
                "ending_reason",
                "data_and_access_handling",
                "replacement_solution",
                "final_assessment",
                "lessons_learned",
                "early_go_live_exception_confirmed",
                "early_go_live_original_pilot_end",
                "early_go_live_evidence_basis",
                "early_go_live_unobserved_risks",
                "early_go_live_mitigation_measures",
            ]:
                self.fields.pop(name, None)
        elif use_case.status != UseCase.Status.REVIEW:
            self.fields.pop("pilot_start", None)

        selected_decision = self.fields["decision"].initial
        if self.is_bound:
            selected_decision = self.data.get("decision")
        early_exception_visible = bool(
            use_case.status == UseCase.Status.PILOT
            and use_case.planned_pilot_end
            and use_case.planned_pilot_end > today
            and (requested_action == "go_live" or selected_decision == Review.Decision.GO_LIVE)
        )
        if not early_exception_visible:
            for name in [
                "early_go_live_exception_confirmed",
                "early_go_live_original_pilot_end",
                "early_go_live_evidence_basis",
                "early_go_live_unobserved_risks",
                "early_go_live_mitigation_measures",
            ]:
                self.fields.pop(name, None)
        elif not can_confirm_early_go_live_exception(actor):
            exception_field = self.fields["early_go_live_exception_confirmed"]
            exception_field.disabled = True
            exception_field.help_text = (
                "Eine vorzeitige Produktivsetzung darf ausschließlich ein Mitglied der "
                "Gruppe KI-Koordinator bestätigen."
            )

        user_model = get_user_model()
        self.fields["action_owner"].queryset = user_model.objects.filter(
            is_active=True, is_anonymized=False
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        for name in ["decision", "new_status", "action_owner"]:
            if name in self.fields and not self.fields[name].widget.is_hidden:
                self.fields[name].widget.attrs["class"] = "form-select"
        for name in [
            "go_live_exception_confirmed",
            "early_go_live_exception_confirmed",
        ]:
            if name in self.fields and not self.fields[name].widget.is_hidden:
                self.fields[name].widget.attrs["class"] = "form-check-input"
        if (
            "go_live_exception_confirmed" in self.fields
            and not self.fields["go_live_exception_confirmed"].widget.is_hidden
        ):
            exception_field = self.fields["go_live_exception_confirmed"]
            if not can_confirm_go_live_exception(actor):
                exception_field.disabled = True
                exception_field.help_text = (
                    "Eine Go-live-Ausnahme darf ausschließlich ein Mitglied der Gruppe "
                    "KI-Koordinator bestätigen."
                )

    def clean(self):
        cleaned = super().clean()
        if self.pilot_start_only:
            cleaned["decision"] = Review.Decision.START_PILOT
            cleaned["new_status"] = UseCase.Status.PILOT
            cleaned["go_live_exception_confirmed"] = False
        decision = cleaned.get("decision")
        new_status = cleaned.get("new_status")
        expected = {
            Review.Decision.START_REVIEW: UseCase.Status.REVIEW,
            Review.Decision.START_PILOT: UseCase.Status.PILOT,
            Review.Decision.GO_LIVE: UseCase.Status.OPERATION,
            Review.Decision.END: UseCase.Status.ENDED,
        }.get(decision)
        if expected and new_status != expected:
            self.add_error(
                "new_status",
                f"Diese Entscheidung erfordert den Status {UseCase.Status(expected).label}.",
            )
        if (
            decision in {Review.Decision.PAUSE, Review.Decision.REWORK, Review.Decision.CONTINUE}
            and new_status != self.use_case.status
        ):
            self.add_error(
                "new_status",
                "Fortführen, Pausieren und Überarbeiten ändern den Lifecycle-Status nicht.",
            )
        if decision == Review.Decision.RETURN:
            order = {
                UseCase.Status.IDEA: 0,
                UseCase.Status.REVIEW: 1,
                UseCase.Status.PILOT: 2,
                UseCase.Status.OPERATION: 3,
                UseCase.Status.ENDED: 4,
            }
            if not new_status or order[new_status] >= order[self.use_case.status]:
                self.add_error(
                    "new_status",
                    "Für eine Rückstufung muss eine frühere Lifecycle-Phase gewählt werden.",
                )
        if decision == Review.Decision.START_PILOT:
            pilot_start = cleaned.get("pilot_start")
            if pilot_start is None:
                self.add_error("pilot_start", "Der tatsächliche Pilotbeginn ist erforderlich.")
            else:
                try:
                    validate_pilot_start_date(use_case=self.use_case, pilot_start=pilot_start)
                except ValidationError as exc:
                    self.add_error("pilot_start", exc)
        else:
            cleaned["pilot_start"] = None

        exception_required = (
            decision == Review.Decision.GO_LIVE
            and self.use_case.metric_result == UseCase.MetricResult.NOT_ACHIEVED
        )
        if exception_required and not can_confirm_go_live_exception(self.actor):
            self.add_error(
                "go_live_exception_confirmed",
                "Nur ein KI-Koordinator darf die erforderliche Go-live-Ausnahme bestätigen.",
            )
        elif exception_required and not cleaned.get("go_live_exception_confirmed"):
            self.add_error(
                "go_live_exception_confirmed",
                "Die Ausnahme muss bei verfehltem Pilotziel ausdrücklich bestätigt werden.",
            )
        if not exception_required:
            cleaned["go_live_exception_confirmed"] = False

        early_exception_required = bool(
            decision == Review.Decision.GO_LIVE
            and self.use_case.planned_pilot_end
            and self.use_case.planned_pilot_end > timezone.localdate()
        )
        if early_exception_required:
            if not can_confirm_early_go_live_exception(self.actor):
                self.add_error(
                    "early_go_live_exception_confirmed",
                    "Nur ein KI-Koordinator darf eine vorzeitige Produktivsetzung bestätigen.",
                )
            elif not cleaned.get("early_go_live_exception_confirmed"):
                self.add_error(
                    "early_go_live_exception_confirmed",
                    "Die vorzeitige Produktivsetzung muss ausdrücklich bestätigt werden.",
                )
            for field_name in [
                "early_go_live_evidence_basis",
                "early_go_live_unobserved_risks",
                "early_go_live_mitigation_measures",
            ]:
                if not str(cleaned.get(field_name, "")).strip():
                    self.add_error(field_name, "Dieses Feld ist für die Ausnahme erforderlich.")
            cleaned["early_go_live_original_pilot_end"] = self.use_case.planned_pilot_end
        else:
            cleaned["early_go_live_exception_confirmed"] = False
            cleaned["early_go_live_original_pilot_end"] = None
            cleaned["early_go_live_evidence_basis"] = ""
            cleaned["early_go_live_unobserved_risks"] = ""
            cleaned["early_go_live_mitigation_measures"] = ""

        if decision == Review.Decision.END:
            for field in ["ending_reason", "data_and_access_handling"]:
                if not cleaned.get(field):
                    self.add_error(field, "Dieses Feld ist für die Beendigung erforderlich.")
        return cleaned
