from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from ki_radar.accelerator.solution_generation_entry import (
    build_solution_generation_entry_context,
)

from .forms import SolutionSelectionForm
from .models import ProcessAnalysis
from .permissions import can_edit_value_stream
from .solution_selection import (
    comparison_blockers,
    ordered_solution_options,
    select_preferred_solution,
)


@login_required
def solution_option_compare(request, pk):
    process_analysis = get_object_or_404(
        ProcessAnalysis.objects.select_related(
            "stage__value_stream__focus",
            "stage__value_stream__owner",
        ).prefetch_related(
            "validations",
            "solution_options",
            "solution_selection_decisions__selected_option",
            "solution_selection_decisions__decided_by",
        ),
        pk=pk,
    )
    options = ordered_solution_options(process_analysis)
    blockers = comparison_blockers(options)
    can_select = can_edit_value_stream(
        request.user,
        process_analysis.stage.value_stream,
    )
    generation_entry = build_solution_generation_entry_context(process_analysis)

    form = SolutionSelectionForm(request.POST or None, options=options)
    if request.method == "POST":
        if not can_select:
            raise PermissionDenied
        if form.is_valid():
            try:
                select_preferred_solution(
                    process_analysis=process_analysis,
                    selected_option=form.cleaned_data["selected_option"],
                    rationale=form.cleaned_data["rationale"],
                    actor=request.user,
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(
                    request,
                    "Die bevorzugte Lösungsoption wurde auditierbar ausgewählt.",
                )
                return redirect(process_analysis)
    return render(
        request,
        "architecture/solution_option_compare.html",
        {
            "process_analysis": process_analysis,
            "options": options,
            "blockers": blockers,
            "form": form,
            "can_select": can_select,
            "selection_history": process_analysis.solution_selection_decisions.all(),
            **generation_entry,
        },
    )
