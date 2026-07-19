from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import UseCase


@admin.register(UseCase)
class UseCaseAdmin(SimpleHistoryAdmin):
    list_display = ("short_id", "title", "status", "business_unit", "business_owner", "next_review_date", "updated_at")
    list_filter = ("status", "priority", "business_unit", "business_value", "risk_complexity")
    search_fields = ("short_id", "title", "problem_statement", "expected_benefit")
    readonly_fields = ("short_id", "created_at", "updated_at")
