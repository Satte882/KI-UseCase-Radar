from django import forms

from .models import DeliveryPackage

FORM_CONTROL = "form-control"
DELIVERY_PACKAGE_FIELDS = [
    "problem_context",
    "target_outcome",
    "in_scope",
    "out_of_scope",
    "users_and_scenarios",
    "solution_outline",
    "system_context",
    "data_context",
    "integrations",
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
    "dependencies",
    "risks",
    "assumptions",
    "architecture_decisions",
    "initial_backlog",
    "external_delivery_url",
    "handover_notes",
]


class DeliveryPackageForm(forms.ModelForm):
    class Meta:
        model = DeliveryPackage
        fields = DELIVERY_PACKAGE_FIELDS
        widgets = {
            name: forms.Textarea(attrs={"rows": 4})
            for name in DELIVERY_PACKAGE_FIELDS
            if name != "external_delivery_url"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", FORM_CONTROL)
        self.fields["functional_requirements"].widget.attrs["rows"] = 7
        self.fields["acceptance_criteria"].widget.attrs["rows"] = 7
        self.fields["initial_backlog"].widget.attrs["rows"] = 7
