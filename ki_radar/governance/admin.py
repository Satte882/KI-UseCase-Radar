from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import GovernanceAssessment


@admin.register(GovernanceAssessment)
class GovernanceAssessmentAdmin(SimpleHistoryAdmin):
    list_display = ("use_case", "assessment_date", "reviewer", "result", "next_assessment_date")
    list_filter = ("result", "privacy_review_required", "security_review_required", "legal_review_required")
    search_fields = ("use_case__short_id", "use_case__title", "rationale")
