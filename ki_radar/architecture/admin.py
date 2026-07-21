from django.contrib import admin

from .models import UseCaseOrigin, ValueStream, ValueStreamStage


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


@admin.register(UseCaseOrigin)
class UseCaseOriginAdmin(admin.ModelAdmin):
    list_display = ("use_case", "stage", "created_at")
    search_fields = ("use_case__short_id", "use_case__title", "stage__name")
    readonly_fields = ("use_case", "stage", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
