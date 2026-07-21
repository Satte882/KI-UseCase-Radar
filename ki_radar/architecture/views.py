from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render

from ki_radar.use_cases.intake_views import SESSION_KEY
from ki_radar.use_cases.models import UseCase
from ki_radar.use_cases.permissions import can_create_use_case

from .forms import (
    ProcessAnalysisForm,
    SolutionOptionForm,
    ValueStreamForm,
    ValueStreamStageForm,
)
from .models import ProcessAnalysis, SolutionOption, ValueStream, ValueStreamStage
from .permissions import can_edit_value_stream, can_manage_architecture

SOLUTION_TYPE_MAP = {
    SolutionOption.OptionType.RULE_AUTOMATION: UseCase.SolutionType.AUTOMATION,
    SolutionOption.OptionType.STANDARD_SOFTWARE: UseCase.SolutionType.STANDARD,
    SolutionOption.OptionType.CUSTOM_SOFTWARE: UseCase.SolutionType.CUSTOM,
    SolutionOption.OptionType.ANALYTICS_ML: UseCase.SolutionType.ANALYTICS,
    SolutionOption.OptionType.GENERATIVE_AI: UseCase.SolutionType.GENERATIVE,
    SolutionOption.OptionType.ASSISTANT: UseCase.SolutionType.ASSISTANT,
}


def _can_edit_process(user, process_analysis: ProcessAnalysis) -> bool:
    return can_edit_value_stream(user, process_analysis.stage.value_stream)


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
            "stages__use_case_origins__use_case",
            "stages__process_analyses__solution_options",
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
        {
            "form": form,
            "title": "Value Stream bearbeiten",
            "value_stream": value_stream,
        },
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


@login_required
def process_analysis_create(request, stage_id):
    stage = get_object_or_404(
        ValueStreamStage.objects.select_related("value_stream"),
        pk=stage_id,
    )
    if not can_edit_value_stream(request.user, stage.value_stream):
        raise PermissionDenied
    form = ProcessAnalysisForm(
        request.POST or None,
        initial={
            "name": f"Prozessanalyse: {stage.name}",
            "trigger": stage.value_stream.trigger,
            "outcome": stage.description or stage.value_stream.outcome,
            "roles": stage.actors,
            "systems": stage.systems,
            "data_objects": stage.documents,
            "bottlenecks": stage.pain_points,
            "baseline_metrics": stage.baseline_metrics,
        },
    )
    if request.method == "POST" and form.is_valid():
        process_analysis = form.save(commit=False)
        process_analysis.stage = stage
        process_analysis.analyzed_by = request.user
        process_analysis.save()
        messages.success(request, "Prozessanalyse wurde angelegt.")
        return redirect(process_analysis)
    return render(
        request,
        "architecture/process_analysis_form.html",
        {"form": form, "stage": stage, "title": "Prozessanalyse anlegen"},
    )


@login_required
def process_analysis_detail(request, pk):
    process_analysis = get_object_or_404(
        ProcessAnalysis.objects.select_related(
            "stage__value_stream__business_unit", "analyzed_by"
        ).prefetch_related("solution_options", "use_case_origins__use_case"),
        pk=pk,
    )
    return render(
        request,
        "architecture/process_analysis_detail.html",
        {
            "process_analysis": process_analysis,
            "can_edit": _can_edit_process(request.user, process_analysis),
            "can_create_use_case": can_create_use_case(request.user),
        },
    )


@login_required
def process_analysis_update(request, pk):
    process_analysis = get_object_or_404(
        ProcessAnalysis.objects.select_related("stage__value_stream"),
        pk=pk,
    )
    if not _can_edit_process(request.user, process_analysis):
        raise PermissionDenied
    form = ProcessAnalysisForm(request.POST or None, instance=process_analysis)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Prozessanalyse wurde aktualisiert.")
        return redirect(process_analysis)
    return render(
        request,
        "architecture/process_analysis_form.html",
        {
            "form": form,
            "stage": process_analysis.stage,
            "process_analysis": process_analysis,
            "title": "Prozessanalyse bearbeiten",
        },
    )


@login_required
def solution_option_create(request, process_analysis_id):
    process_analysis = get_object_or_404(
        ProcessAnalysis.objects.select_related("stage__value_stream"),
        pk=process_analysis_id,
    )
    if not _can_edit_process(request.user, process_analysis):
        raise PermissionDenied
    form = SolutionOptionForm(request.POST or None, process_analysis=process_analysis)
    if request.method == "POST" and form.is_valid():
        option = form.save(commit=False)
        option.process_analysis = process_analysis
        option.created_by = request.user
        option.save()
        messages.success(request, "Lösungsoption wurde ergänzt.")
        return redirect(process_analysis)
    return render(
        request,
        "architecture/solution_option_form.html",
        {
            "form": form,
            "process_analysis": process_analysis,
            "title": "Lösungsoption ergänzen",
        },
    )


@login_required
def solution_option_update(request, pk):
    option = get_object_or_404(
        SolutionOption.objects.select_related("process_analysis__stage__value_stream"),
        pk=pk,
    )
    if not _can_edit_process(request.user, option.process_analysis):
        raise PermissionDenied
    form = SolutionOptionForm(
        request.POST or None,
        instance=option,
        process_analysis=option.process_analysis,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lösungsoption wurde aktualisiert.")
        return redirect(option.process_analysis)
    return render(
        request,
        "architecture/solution_option_form.html",
        {
            "form": form,
            "process_analysis": option.process_analysis,
            "option": option,
            "title": "Lösungsoption bearbeiten",
        },
    )


@login_required
def solution_option_start_use_case(request, pk):
    if not can_create_use_case(request.user):
        raise PermissionDenied
    option = get_object_or_404(
        SolutionOption.objects.select_related(
            "process_analysis__stage__value_stream__business_unit"
        ),
        pk=pk,
    )
    if option.recommendation != SolutionOption.Recommendation.PREFERRED:
        messages.warning(
            request,
            "Nur eine ausdrücklich bevorzugte Lösungsoption kann in den Use-Case-Intake überführt werden.",
        )
        return redirect(option.process_analysis)
    process_analysis = option.process_analysis
    stage = process_analysis.stage
    stored = {
        "title": option.name,
        "business_unit": stage.value_stream.business_unit_id,
        "problem_statement": process_analysis.bottlenecks,
        "affected_process": process_analysis.name,
        "summary": process_analysis.current_flow,
        "target_users": process_analysis.roles,
        "source_systems": process_analysis.systems,
        "intended_users": process_analysis.roles,
        "intended_purpose": option.description,
        "expected_benefit": option.expected_value,
        "data_sources": option.data_requirements or process_analysis.data_objects,
        "solution_type": SOLUTION_TYPE_MAP.get(option.option_type, UseCase.SolutionType.OTHER),
        "source_stage_id": str(stage.pk),
        "source_process_analysis_id": str(process_analysis.pk),
        "source_solution_option_id": str(option.pk),
    }
    request.session[SESSION_KEY] = stored
    request.session.modified = True
    messages.info(
        request,
        "Der Intake wurde aus der bevorzugten Lösungsoption vorbefüllt. Die bestehende Bewertung und Governance bleiben verbindlich.",
    )
    return redirect("use_cases:create")
