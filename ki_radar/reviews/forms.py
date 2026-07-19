from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from ki_radar.use_cases.models import UseCase
from .models import Review


class ReviewForm(forms.ModelForm):
    ending_reason = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Beendigungsgrund")
    data_and_access_handling = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Umgang mit Daten und Zugängen")
    replacement_solution = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Ersatzlösung")
    final_assessment = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Abschlussbewertung")
    lessons_learned = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Lessons Learned")
    class Meta:
        model = Review
        fields = ["review_date", "decision", "new_status", "rationale", "open_actions", "action_owner", "action_due_date", "next_review_date"]
        widgets = {
            "review_date": forms.DateInput(attrs={"type": "date"}),
            "action_due_date": forms.DateInput(attrs={"type": "date"}),
            "next_review_date": forms.DateInput(attrs={"type": "date"}),
            "rationale": forms.Textarea(attrs={"rows": 4}),
            "open_actions": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, use_case: UseCase, **kwargs):
        self.use_case = use_case
        super().__init__(*args, **kwargs)
        self.fields["review_date"].initial = timezone.localdate()
        self.fields["new_status"].initial = use_case.status
        User = get_user_model()
        self.fields["action_owner"].queryset = User.objects.filter(is_active=True, is_anonymized=False)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        decision = cleaned.get("decision")
        new_status = cleaned.get("new_status")
        expected = {
            Review.Decision.START_REVIEW: UseCase.Status.REVIEW,
            Review.Decision.START_PILOT: UseCase.Status.PILOT,
            Review.Decision.GO_LIVE: UseCase.Status.OPERATION,
            Review.Decision.END: UseCase.Status.ENDED,
        }.get(decision)
        if expected and new_status != expected:
            self.add_error("new_status", f"Diese Entscheidung erfordert den Status {UseCase.Status(expected).label}.")
        if decision in {Review.Decision.PAUSE, Review.Decision.REWORK, Review.Decision.CONTINUE} and new_status != self.use_case.status:
            self.add_error("new_status", "Fortführen, Pausieren und Überarbeiten ändern den Lifecycle-Status nicht.")
        if decision == Review.Decision.RETURN:
            order = {UseCase.Status.IDEA: 0, UseCase.Status.REVIEW: 1, UseCase.Status.PILOT: 2, UseCase.Status.OPERATION: 3, UseCase.Status.ENDED: 4}
            if not new_status or order[new_status] >= order[self.use_case.status]:
                self.add_error("new_status", "Für eine Rückstufung muss eine frühere Lifecycle-Phase gewählt werden.")
        if decision == Review.Decision.END:
            for field in ["ending_reason", "data_and_access_handling"]:
                if not cleaned.get(field):
                    self.add_error(field, "Dieses Feld ist für die Beendigung erforderlich.")
        return cleaned
