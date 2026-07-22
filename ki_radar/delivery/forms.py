from django import forms

from .architecture_artifacts import get_delivery_architecture_artifacts
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
    "system_landscape",
    "data_context",
    "data_flows",
    "integrations",
    "integration_contracts",
    "architecture_artifacts_url",
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
    system_landscape = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Ist-/Ziel-Systemlandschaft",
    )
    data_flows = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Daten- und Informationsflüsse",
    )
    integration_contracts = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Integrationsverträge und Verantwortlichkeiten",
    )
    architecture_artifacts_url = forms.URLField(
        required=False,
        label="Architekturartefakte und Diagramme",
    )

    class Meta:
        model = DeliveryPackage
        fields = DELIVERY_PACKAGE_FIELDS
        widgets = {
            name: forms.Textarea(attrs={"rows": 4})
            for name in DELIVERY_PACKAGE_FIELDS
            if name not in {
                "external_delivery_url",
                "architecture_artifacts_url",
                "system_landscape",
                "data_flows",
                "integration_contracts",
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        artifacts = (
            get_delivery_architecture_artifacts(self.instance)
            if self.instance.pk
            else None
        )
        if artifacts is not None and not self.is_bound:
            self.initial.update(
                {
                    "system_landscape": artifacts.system_landscape,
                    "data_flows": artifacts.data_flows,
                    "integration_contracts": artifacts.integration_contracts,
                    "architecture_artifacts_url": artifacts.artifacts_url,
                }
            )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", FORM_CONTROL)
        self.fields["functional_requirements"].widget.attrs["rows"] = 7
        self.fields["acceptance_criteria"].widget.attrs["rows"] = 7
        self.fields["initial_backlog"].widget.attrs["rows"] = 7

    def save(self, commit=True):
        package = super().save(commit=False)
        package._architecture_artifacts_payload = {
            "system_landscape": self.cleaned_data["system_landscape"],
            "data_flows": self.cleaned_data["data_flows"],
            "integration_contracts": self.cleaned_data["integration_contracts"],
            "artifacts_url": self.cleaned_data.get("architecture_artifacts_url", ""),
        }
        if commit:
            package.save()
            self.save_m2m()
        return package
