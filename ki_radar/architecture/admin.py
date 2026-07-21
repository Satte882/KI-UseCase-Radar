from django.contrib import admin

from .models import ValueStream, ValueStreamStage


class ValueStreamStageInline(admin.TabularInline):
    model = ValueStreamStage
    extra = 0
    fields = ("sequence", "name", "actors", "systems", "pain_points")


@admin.register(ValueStream)
class ValueStreamAdmin(admin.ModelAdmin):
    list_display = ("name", "business_unit", "owner", "status", "updated_at")
    list_filter = ("status", "business_unit")
    search_fields = ("name", "description", "strategic_objective")
    inlines = [ValueStreamStageInline]


@admin.register(ValueStreamStage)
class ValueStreamStageAdmin(admin.ModelAdmin):
    list_display = ("value_stream", "sequence", "name", "updated_at")
    list_filter = ("value_stream__business_unit",)
    search_fields = ("name", "description", "pain_points")
