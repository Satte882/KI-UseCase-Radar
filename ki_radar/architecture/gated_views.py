from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from . import views
from .models import ValueStream, ValueStreamStage

PHASE_COMPLETION_REQUIRED_MESSAGE = (
    "Der Value Stream ist noch im Entwurf. Ergänze zuerst die End-to-End-Phasen "
    "und setze den Status anschließend auf Aktiv."
)


def _active_stage_or_redirect(request, pk):
    stage = get_object_or_404(
        ValueStreamStage.objects.select_related("value_stream"),
        pk=pk,
    )
    if stage.value_stream.status != ValueStream.Status.ACTIVE:
        messages.warning(request, PHASE_COMPLETION_REQUIRED_MESSAGE)
        return stage, redirect(stage.value_stream)
    return stage, None


@login_required
def stage_start_use_case(request, pk):
    _stage, blocked_response = _active_stage_or_redirect(request, pk)
    if blocked_response is not None:
        return blocked_response
    return views.stage_start_use_case(request, pk=pk)


@login_required
def process_analysis_create(request, stage_id):
    _stage, blocked_response = _active_stage_or_redirect(request, stage_id)
    if blocked_response is not None:
        return blocked_response
    return views.process_analysis_create(request, stage_id=stage_id)
