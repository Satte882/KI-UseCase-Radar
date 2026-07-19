from django import forms
from django.contrib.auth import get_user_model

from ki_radar.accounts.models import BusinessUnit
from ki_radar.accounts.permissions import is_coordinator

from .models import UseCase


class DateInput(forms.DateInput):
    input_type = "date"


class UseCaseForm(forms.ModelForm):
    class Meta:
        model = UseCase
        exclude = [
            "id",
            "short_id",
            "status",
            "submitter",
            "created_at",
            "updated_at",
            "actual_end_date",
            "ending_reason",
            "final_assessment",
            "lessons_learned",
            "data_and_access_handling",
            "replacement_solution",
            "is_archived",
            "privacy_review_required",
            "security_review_required",
            "legal_review_required",
        ]
        widgets = {
            "next_review_date": DateInput(),
            "pilot_start": DateInput(),
            "planned_pilot_end": DateInput(),
            "problem_statement": forms.Textarea(attrs={"rows": 4}),
            "summary": forms.Textarea(attrs={"rows": 2}),
            "expected_benefit": forms.Textarea(attrs={"rows": 3}),
            "baseline": forms.Textarea(attrs={"rows": 2}),
            "success_criterion": forms.Textarea(attrs={"rows": 2}),
            "human_oversight": forms.Textarea(attrs={"rows": 2}),
            "support_responsibility": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-control"
                if not isinstance(field.widget, forms.CheckboxInput)
                else "form-check-input",
            )
        self.fields["business_unit"].queryset = BusinessUnit.objects.filter(is_active=True)
        User = get_user_model()
        active_users = User.objects.filter(is_active=True, is_anonymized=False).order_by(
            "last_name", "first_name", "username"
        )
        for name in ["business_owner", "coordinator", "technical_owner"]:
            self.fields[name].queryset = active_users
        self.fields["business_owner"].required = True
        if current_user and not self.instance.pk:
            self.fields["business_owner"].initial = current_user
        if current_user and not is_coordinator(current_user):
            for name in [
                "business_owner",
                "coordinator",
                "privacy_review_completed",
                "security_review_completed",
                "legal_review_completed",
            ]:
                if name in self.fields:
                    self.fields[name].disabled = True

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("pilot_start")
        end = cleaned.get("planned_pilot_end")
        if start and end and end < start:
            self.add_error(
                "planned_pilot_end", "Das geplante Pilotende darf nicht vor dem Pilotbeginn liegen."
            )
        return cleaned
