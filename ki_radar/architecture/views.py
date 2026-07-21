from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render

from ki_radar.use_cases.intake_views import SESSION_KEY
from ki_radar.use_cases.permissions import can_create_use_case

from .forms import ValueStreamForm, ValueStreamStageForm
from .models import ValueStream, ValueStreamStage
from .permissions import can_edit_value_stream, can_manage_architecture


@login_required
def value_stream_list(request):
    value_streams = (
        ValueStream.objects.select_related("business_unit", "owner")
        .annotate(stage_total=Count("stages"))
        .order_by("business_unit__name", "name")
    )
    return render(
        request,
        "architecture/value_stream_list.html",
        {
            "value_streams": value_streams,
            "can_create": can_manage_architecture(request.user),
        },
    )


@login_required
def value_stream_detail(request, pk):
    value_stream = get_object_or_404(
        ValueStream.objects.select_related("business_unit", "owner", "created_by").prefetch_related(
            "stages__use_case_origins__use_case"
        ),
        pk=pk,
    )
    return render(
        request,
        "architecture/value_stream_detail.html",
        {
            "value_stream": value_stream,
            "can_edit": can_edit_value_stream(request.user, value_stream),
            "can_create_use_case": can_create_use_case(request.user),
        },
    )


@login_required
def value_stream_create(request):
    if not can_manage_architecture(request.user):
        raise PermissionDenied
    form = ValueStreamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        value_stream = form.save(commit=False)
        value_stream.created_by = request.user
        if value_stream.owner_id is None:
            value_stream.owner = request.user
        value_stream.save()
        messages.success(request, "Value Stream wurde angelegt.")
        return redirect(value_stream)
    return render(
        request,
        "architecture/value_stream_form.html",
        {"form": form, "title": "Value Stream anlegen"},
    )


@login_required
def value_stream_update(request, pk):
    value_stream = get_object_or_404(ValueStream, pk=pk)
    if not can_edit_value_stream(request.user, value_stream):
        raise PermissionDenied
    form = ValueStreamForm(request.POST or None, instance=value_stream)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Value Stream wurde aktualisiert.")
        return redirect(value_stream)
    return render(
        request,
        "architecture/value_stream_form.html",
        {"form": form, "title": "Value Stream bearbeiten", "value_stream": value_stream},
    )


@login_required
def stage_create(request, value_stream_id):
    value_stream = get_object_or_404(ValueStream, pk=value_stream_id)
    if not can_edit_value_stream(request.user, value_stream):
        raise PermissionDenied
    max_sequence = value_stream.stages.aggregate(max_sequence=Max("sequence"))["max_sequence"] or 0
    form = ValueStreamStageForm(request.POST or None, initial={"sequence": max_sequence + 1})
    if request.method == "POST" and form.is_valid():
        stage = form.save(commit=False)
        stage.value_stream = value_stream
        stage.save()
        messages.success(request, "Value-Stream-Phase wurde ergänzt.")
        return redirect(value_stream)
    return render(
        request,
        "architecture/stage_form.html",
        {"form": form, "value_stream": value_stream, "title": "Phase ergänzen"},
    )


@login_required
def stage_update(request, pk):
    stage = get_object_or_404(ValueStreamStage.objects.select_related("value_stream"), pk=pk)
    if not can_edit_value_stream(request.user, stage.value_stream):
        raise PermissionDenied
    form = ValueStreamStageForm(request.POST or None, instance=stage)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Value-Stream-Phase wurde aktualisiert.")
        return redirect(stage.value_stream)
    return render(
        request,
        "architecture/stage_form.html",
        {
            "form": form,
            "value_stream": stage.value_stream,
            "stage": stage,
            "title": "Phase bearbeiten",
        },
    )


@login_required
def stage_start_use_case(request, pk):
    if not can_create_use_case(request.user):
        raise PermissionDenied
    stage = get_object_or_404(
        ValueStreamStage.objects.select_related("value_stream__business_unit"),
        pk=pk,
    )
    stored = {
        "title": f"{stage.name}: KI-Potenzial",
        "business_unit": stage.value_stream.business_unit_id,
        "affected_process": stage.name,
        "summary": stage.description,
        "target_users": stage.actors,
        "source_systems": stage.systems,
        "source_stage_id": str(stage.pk),
    }
    if stage.pain_points.strip():
        stored["problem_statement"] = stage.pain_points.strip()
    request.session[SESSION_KEY] = stored
    request.session.modified = True
    messages.info(
        request,
        "Der Intake wurde aus der Value-Stream-Phase vorbefüllt. Alle Angaben bleiben editierbar.",
    )
    return redirect("use_cases:create")
