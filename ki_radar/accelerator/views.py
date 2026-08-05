from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ki_radar.architecture.permissions import can_manage_architecture
from ki_radar.use_cases.permissions import can_create_use_case

from .catalogs import (
    CaptureAnswerValidationError,
    UnsupportedCaptureCatalog,
    get_capture_catalog,
)
from .forms import CaptureSectionForm, CaptureStartForm
from .models import CaptureSession
from .services import (
    CaptureRevisionConflict,
    CaptureStateError,
    complete_capture_session,
    create_capture_session,
    discard_capture_session,
    get_owned_capture_session,
    save_capture_session,
)

SUPPORTED_UI_CAPTURE_TYPES = {CaptureSession.CaptureType.VALUE_STREAM}


def _can_start_capture(actor, capture_type: str) -> bool:
    if capture_type == CaptureSession.CaptureType.VALUE_STREAM:
        return can_manage_architecture(actor)
    if capture_type == CaptureSession.CaptureType.USE_CASE:
        return can_create_use_case(actor)
    return False


def _load_ui_session(*, actor, session_id) -> CaptureSession:
    try:
        session = get_owned_capture_session(actor=actor, session_id=session_id)
    except CaptureSession.DoesNotExist as exc:
        raise Http404 from exc
    if session.capture_type not in SUPPORTED_UI_CAPTURE_TYPES:
        raise Http404
    return session


def _step_states(catalog, session: CaptureSession, current_step: int) -> list[dict]:
    states = []
    for number, section in enumerate(catalog.sections, start=1):
        required_keys = [question.key for question in section.questions if question.required]
        complete = all(session.answers.get(key, "").strip() for key in required_keys)
        states.append(
            {
                "number": number,
                "title": section.title,
                "complete": complete,
                "current": number == current_step,
            }
        )
    return states


def _review_sections(catalog, session: CaptureSession) -> list[dict]:
    return [
        {
            "title": section.title,
            "questions": [
                {
                    "label": question.label,
                    "required": question.required,
                    "answer": session.answers.get(question.key, ""),
                }
                for question in section.questions
            ],
        }
        for section in catalog.sections
    ]


@login_required
def start_capture(request, capture_type: str):
    if capture_type not in SUPPORTED_UI_CAPTURE_TYPES:
        raise Http404
    if not _can_start_capture(request.user, capture_type):
        raise PermissionDenied
    if request.method == "POST":
        form = CaptureStartForm(request.POST)
        if form.is_valid():
            session = create_capture_session(
                actor=request.user,
                capture_type=capture_type,
                working_title=form.cleaned_data["working_title"],
            )
            return redirect("accelerator:capture_step", session_id=session.pk, step=1)
    else:
        form = CaptureStartForm()
    return render(
        request,
        "accelerator/capture_start.html",
        {
            "form": form,
            "capture_type": capture_type,
            "capture_label": "Value Stream",
        },
    )


@login_required
def capture_step(request, session_id, step: int):
    session = _load_ui_session(actor=request.user, session_id=session_id)
    if session.status != CaptureSession.Status.DRAFT:
        return redirect("accelerator:capture_review", session_id=session.pk)
    try:
        catalog = get_capture_catalog(session.capture_type, session.catalog_version)
    except UnsupportedCaptureCatalog:
        return redirect("accelerator:capture_review", session_id=session.pk)
    if step < 1 or step > len(catalog.sections):
        return redirect("accelerator:capture_step", session_id=session.pk, step=1)

    section = catalog.sections[step - 1]
    conflict_message = ""
    response_status = 200
    if request.method == "POST":
        form = CaptureSectionForm(
            request.POST,
            section=section,
            initial_answers=session.answers,
            revision=session.revision,
        )
        if form.is_valid():
            try:
                session = save_capture_session(
                    actor=request.user,
                    session_id=session.pk,
                    expected_revision=form.cleaned_data["revision"],
                    answer_updates=form.cleaned_answer_updates(),
                )
            except CaptureRevisionConflict as exc:
                session = _load_ui_session(actor=request.user, session_id=session_id)
                conflict_message = str(exc)
                response_status = 409
            except (CaptureAnswerValidationError, CaptureStateError) as exc:
                form.add_error(None, str(exc))
            else:
                action = request.POST.get("action", "next")
                if action == "save":
                    messages.success(request, "Zwischenstand gespeichert.")
                    return redirect(
                        "accelerator:capture_step",
                        session_id=session.pk,
                        step=step,
                    )
                if step == len(catalog.sections):
                    return redirect("accelerator:capture_review", session_id=session.pk)
                return redirect(
                    "accelerator:capture_step",
                    session_id=session.pk,
                    step=step + 1,
                )
    else:
        form = CaptureSectionForm(
            section=section,
            initial_answers=session.answers,
            revision=session.revision,
        )

    return render(
        request,
        "accelerator/capture_wizard.html",
        {
            "session": session,
            "catalog": catalog,
            "section": section,
            "form": form,
            "step": step,
            "total_steps": len(catalog.sections),
            "step_states": _step_states(catalog, session, step),
            "previous_step": step - 1 if step > 1 else None,
            "is_last_step": step == len(catalog.sections),
            "conflict_message": conflict_message,
        },
        status=response_status,
    )


@login_required
def capture_review(request, session_id):
    session = _load_ui_session(actor=request.user, session_id=session_id)
    completion_errors: tuple[str, ...] = ()
    conflict_message = ""
    response_status = 200
    try:
        catalog = get_capture_catalog(session.capture_type, session.catalog_version)
        catalog_error = ""
    except UnsupportedCaptureCatalog as exc:
        catalog = None
        catalog_error = str(exc)

    if request.method == "POST" and request.POST.get("action") == "complete":
        if catalog is None:
            completion_errors = (catalog_error,)
        else:
            try:
                expected_revision = int(request.POST.get("revision", "-1"))
                session = complete_capture_session(
                    actor=request.user,
                    session_id=session.pk,
                    expected_revision=expected_revision,
                )
            except CaptureAnswerValidationError as exc:
                completion_errors = exc.errors
            except CaptureRevisionConflict as exc:
                session = _load_ui_session(actor=request.user, session_id=session_id)
                conflict_message = str(exc)
                response_status = 409
            except CaptureStateError as exc:
                completion_errors = (str(exc),)
            else:
                messages.success(request, "Die Erfassung wurde abgeschlossen.")
                return redirect("accelerator:capture_review", session_id=session.pk)

    return render(
        request,
        "accelerator/capture_review.html",
        {
            "session": session,
            "catalog": catalog,
            "catalog_error": catalog_error,
            "sections": _review_sections(catalog, session) if catalog else [],
            "completion_errors": completion_errors,
            "conflict_message": conflict_message,
        },
        status=response_status,
    )


@login_required
@require_POST
def capture_discard(request, session_id):
    session = _load_ui_session(actor=request.user, session_id=session_id)
    try:
        expected_revision = int(request.POST.get("revision", "-1"))
        discard_capture_session(
            actor=request.user,
            session_id=session.pk,
            expected_revision=expected_revision,
        )
    except CaptureRevisionConflict:
        messages.error(
            request,
            "Die Erfassung wurde zwischenzeitlich geändert und nicht verworfen.",
        )
    except CaptureStateError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Die Erfassung wurde verworfen.")
    return redirect("accelerator:capture_review", session_id=session.pk)
