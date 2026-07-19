from __future__ import annotations

import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import UseCaseForm
from .models import UseCase
from .permissions import can_create_use_case, can_edit_use_case, can_view_use_case


@login_required
def use_case_list(request):
    queryset = UseCase.objects.filter(is_archived=False).select_related("business_unit", "business_owner", "coordinator")
    q = request.GET.get("q", "").strip()
    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(short_id__icontains=q) | Q(problem_statement__icontains=q) | Q(expected_benefit__icontains=q))
    for param, field in {
        "status": "status", "business_unit": "business_unit_id", "business_owner": "business_owner_id",
        "coordinator": "coordinator_id", "business_value": "business_value", "technical_feasibility": "technical_feasibility",
        "data_readiness": "data_readiness", "risk_complexity": "risk_complexity",
    }.items():
        value = request.GET.get(param)
        if value:
            queryset = queryset.filter(**{field: value})
    if request.GET.get("overdue") == "1":
        queryset = queryset.filter(next_review_date__lt=timezone.localdate()).exclude(status=UseCase.Status.ENDED)
    context = {
        "use_cases": queryset,
        "status_choices": UseCase.Status.choices,
        "level_choices": UseCase.Level.choices,
        "can_create": can_create_use_case(request.user),
    }
    return render(request, "use_cases/list.html", context)


@login_required
def use_case_detail(request, pk):
    use_case = get_object_or_404(UseCase.objects.select_related("business_unit", "business_owner", "coordinator", "technical_owner"), pk=pk)
    if not can_view_use_case(request.user, use_case):
        raise PermissionDenied
    history = use_case.history.select_related("history_user").order_by("-history_date")[:50]
    return render(request, "use_cases/detail.html", {"use_case": use_case, "history": history, "can_edit": can_edit_use_case(request.user, use_case)})


@login_required
def use_case_create(request):
    if not can_create_use_case(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = UseCaseForm(request.POST, current_user=request.user)
        if form.is_valid():
            use_case = form.save(commit=False)
            use_case.submitter = request.user
            use_case.save()
            messages.success(request, f"Use Case {use_case.short_id} wurde angelegt.")
            return redirect(use_case)
    else:
        form = UseCaseForm(current_user=request.user)
    return render(request, "use_cases/form.html", {"form": form, "title": "Use Case anlegen"})


@login_required
def use_case_edit(request, pk):
    use_case = get_object_or_404(UseCase, pk=pk)
    if not can_edit_use_case(request.user, use_case):
        raise PermissionDenied
    if request.method == "POST":
        form = UseCaseForm(request.POST, instance=use_case, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Use Case wurde aktualisiert.")
            return redirect(use_case)
    else:
        form = UseCaseForm(instance=use_case, current_user=request.user)
    return render(request, "use_cases/form.html", {"form": form, "title": f"{use_case.short_id} bearbeiten", "use_case": use_case})


@login_required
def export_csv(request):
    queryset = UseCase.objects.filter(is_archived=False).select_related("business_unit", "business_owner")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="ki-radar-use-cases.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["ID", "Titel", "Status", "Organisationseinheit", "Business Owner", "Nächster Review", "Nutzen", "Risiko"])
    for use_case in queryset:
        writer.writerow([
            use_case.short_id, use_case.title, use_case.get_status_display(), use_case.business_unit.name,
            use_case.business_owner.get_display_name(), use_case.next_review_date or "",
            use_case.get_business_value_display(), use_case.get_risk_complexity_display(),
        ])
    return response
