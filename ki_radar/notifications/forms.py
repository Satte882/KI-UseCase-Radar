from django import forms
from .models import EvidenceLink


class EvidenceLinkForm(forms.ModelForm):
    class Meta:
        model = EvidenceLink
        exclude = ["use_case", "created_by", "created_at", "updated_at"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
