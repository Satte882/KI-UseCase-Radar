from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import BenefitMeasurement, DecisionAssessment, StrategicObjective, UseCase


@admin.register(StrategicObjective)
class StrategicObjectiveAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "is_active",
        "active_from",
        "active_until",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("title", "description", "target_kpi")


@admin.register(UseCase)
class UseCaseAdmin(SimpleHistoryAdmin):
    list_display = (
        "short_id",
        "title",
        "status",
        "business_unit",
        "business_owner",
        "strategic_objective",
        "next_review_date",
        "updated_at",
    )
    list_filter = (
        "status",
        "priority",
        "business_unit",
        "strategic_objective",
        "business_value",
        "risk_complexity",
    )
    search_fields = (
        "short_id",
        "title",
        "problem_statement",
        "expected_benefit",
        "strategic_objective__title",
    )
    readonly_fields = ("short_id", "created_at", "updated_at")


@admin.register(DecisionAssessment)
class DecisionAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "use_case",
        "version",
        "assessment_date",
        "assessed_by",
        "updated_at",
    )
    list_filter = (
        "assessment_date",
        "business_value",
        "strategic_fit",
        "risk_complexity",
    )
    search_fields = ("use_case__short_id", "use_case__title", "overall_rationale")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BenefitMeasurement)
class BenefitMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "use_case",
        "measured_at",
        "actual_value",
        "created_by",
        "updated_at",
    )
    list_filter = ("measured_at",)
    search_fields = (
        "use_case__short_id",
        "use_case__title",
        "period",
        "variance_reason",
    )
    readonly_fields = ("created_at", "updated_at")
