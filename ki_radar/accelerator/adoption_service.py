from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from django.core.exceptions import PermissionDenied
from django.db import transaction

from .adoption_audit import record_adoption_audit
from .adoption_policy import field_adoption_enabled
from .candidate_snapshot import (
    CandidateValidity,
    candidate_validity,
    canonical_text_hash,
    canonicalize_text,
)
from .candidate_state import complete_candidate, reserve_candidate
from .field_registry import UnsupportedAdoptionField, assert_adoptable_field
from .form_adapters import apply_prepared_field_update, prepare_field_update
from .models import (
    CaptureFieldSuggestion,
    CaptureSession,
    FieldAdoptionAudit,
    FieldAdoptionCandidate,
)


class AdoptionDisabled(PermissionDenied):
    pass


class AdoptionOutcome(StrEnum):
    ADOPTED = "adopted"
    ADOPTED_EDITED = "adopted_edited"
    REJECTED = "rejected"
    CONFLICT = "field_conflict"
    STALE = "stale"
    TARGET_MISSING = "target_missing"
    TARGET_INACTIVE = "target_inactive"
    PERMISSION_DENIED = "permission_denied"
    VALIDATION_FAILED = "validation_failed"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"


@dataclass(frozen=True)
class AdoptionResult:
    outcome: AdoptionOutcome
    candidate_id: object
    previous_value: str = ""
    current_value: str = ""
    proposed_value: str = ""
    final_value: str = ""
    target_updated_at_changed: bool = False
    idempotent: bool = False
    errors: dict[str, list[str]] = field(default_factory=dict)


_STATUS_OUTCOMES = {
    FieldAdoptionCandidate.Status.ADOPTED: AdoptionOutcome.ADOPTED,
    FieldAdoptionCandidate.Status.ADOPTED_EDITED: AdoptionOutcome.ADOPTED_EDITED,
    FieldAdoptionCandidate.Status.REJECTED: AdoptionOutcome.REJECTED,
    FieldAdoptionCandidate.Status.CONFLICT: AdoptionOutcome.CONFLICT,
    FieldAdoptionCandidate.Status.STALE: AdoptionOutcome.STALE,
    FieldAdoptionCandidate.Status.PROCESSING: AdoptionOutcome.IN_PROGRESS,
}

_ERROR_OUTCOMES = {
    AdoptionOutcome.CONFLICT.value: AdoptionOutcome.CONFLICT,
    AdoptionOutcome.TARGET_MISSING.value: AdoptionOutcome.TARGET_MISSING,
    AdoptionOutcome.TARGET_INACTIVE.value: AdoptionOutcome.TARGET_INACTIVE,
    AdoptionOutcome.PERMISSION_DENIED.value: AdoptionOutcome.PERMISSION_DENIED,
    AdoptionOutcome.VALIDATION_FAILED.value: AdoptionOutcome.VALIDATION_FAILED,
}


def _candidate_queryset():
    return FieldAdoptionCandidate.objects.select_related(
        "suggestion__analysis__session",
    )


def _bound_target_id(session: CaptureSession):
    if session.capture_type == CaptureSession.CaptureType.VALUE_STREAM:
        return session.target_value_stream_id
    if session.capture_type == CaptureSession.CaptureType.USE_CASE:
        return session.target_use_case_id
    return None


def _candidate_integrity_valid(candidate: FieldAdoptionCandidate) -> bool:
    suggestion = candidate.suggestion
    analysis = suggestion.analysis
    session = analysis.session
    if not isinstance(suggestion.suggested_value, str):
        return False
    suggestion_target_matches = (
        suggestion.target_object_id is None
        or suggestion.target_object_id == candidate.target_object_id
    )
    return bool(
        candidate.target_object_type == suggestion.target_object_type
        and candidate.target_object_type == analysis.capture_type
        and candidate.target_object_type == session.capture_type
        and candidate.target_field == suggestion.target_field
        and suggestion.field_type == CaptureFieldSuggestion.FieldType.TEXT
        and not suggestion.target_group_key
        and suggestion_target_matches
        and candidate.target_object_id == _bound_target_id(session)
        and canonicalize_text(suggestion.suggested_value) == candidate.proposed_value
    )


def _result_from_candidate(candidate: FieldAdoptionCandidate) -> AdoptionResult:
    outcome = _ERROR_OUTCOMES.get(
        candidate.error_code,
        _STATUS_OUTCOMES.get(candidate.status, AdoptionOutcome.FAILED),
    )
    return AdoptionResult(
        outcome=outcome,
        candidate_id=candidate.pk,
        previous_value=candidate.previous_value,
        proposed_value=candidate.proposed_value,
        idempotent=True,
    )


def _form_errors(form) -> dict[str, list[str]]:
    return {name: [str(message) for message in messages] for name, messages in form.errors.items()}


def _complete_result(
    *,
    candidate: FieldAdoptionCandidate,
    actor,
    status: str,
    outcome: AdoptionOutcome,
    action: str = FieldAdoptionAudit.Action.ADOPT,
    error_code: str = "",
    current_value: str = "",
    final_value: str = "",
    edited_value: str | None = None,
    target_updated_at_changed: bool = False,
    errors: dict[str, list[str]] | None = None,
) -> AdoptionResult:
    complete_candidate(
        candidate_id=candidate.pk,
        actor=actor,
        status=status,
        error_code=error_code,
    )
    record_adoption_audit(
        candidate=candidate,
        actor=actor,
        action=action,
        outcome=outcome.value,
        error_code=error_code,
        current_value=current_value,
        final_value=final_value,
        edited_value=edited_value,
        target_updated_at_changed=target_updated_at_changed,
    )
    return AdoptionResult(
        outcome=outcome,
        candidate_id=candidate.pk,
        previous_value=candidate.previous_value,
        current_value=current_value,
        proposed_value=candidate.proposed_value,
        final_value=final_value,
        target_updated_at_changed=target_updated_at_changed,
        errors=errors or {},
    )


def _reserve_and_lock_candidate(*, candidate_id, actor):
    reservation = reserve_candidate(candidate_id=candidate_id, actor=actor)
    if not reservation.acquired:
        return None, _result_from_candidate(reservation.candidate)
    candidate = _candidate_queryset().select_for_update().get(pk=candidate_id)
    return candidate, None


def _lock_target(candidate: FieldAdoptionCandidate):
    spec = assert_adoptable_field(
        target_type=candidate.target_object_type,
        field_name=candidate.target_field,
    )
    try:
        target = spec.model.objects.select_for_update().get(pk=candidate.target_object_id)
    except spec.model.DoesNotExist:
        return spec, None
    return spec, target


def _validity_failure(
    *,
    candidate: FieldAdoptionCandidate,
    actor,
    validity: CandidateValidity,
    action: str = FieldAdoptionAudit.Action.ADOPT,
) -> AdoptionResult | None:
    if validity == CandidateValidity.VALID:
        return None
    if validity == CandidateValidity.TARGET_MISSING:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.STALE,
            outcome=AdoptionOutcome.TARGET_MISSING,
            action=action,
            error_code=AdoptionOutcome.TARGET_MISSING.value,
        )
    if validity == CandidateValidity.TARGET_INACTIVE:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.STALE,
            outcome=AdoptionOutcome.TARGET_INACTIVE,
            action=action,
            error_code=AdoptionOutcome.TARGET_INACTIVE.value,
        )
    return _complete_result(
        candidate=candidate,
        actor=actor,
        status=FieldAdoptionCandidate.Status.STALE,
        outcome=AdoptionOutcome.STALE,
        action=action,
        error_code="stale_candidate",
    )


def _require_enabled() -> None:
    if not field_adoption_enabled():
        raise AdoptionDisabled("Die Feldübernahme ist serverseitig deaktiviert.")


@transaction.atomic
def adopt_field_candidate(
    *,
    candidate_id,
    actor,
    edited_value: str | None = None,
) -> AdoptionResult:
    _require_enabled()
    candidate, existing_result = _reserve_and_lock_candidate(
        candidate_id=candidate_id,
        actor=actor,
    )
    if existing_result is not None:
        return existing_result

    try:
        spec, target = _lock_target(candidate)
    except UnsupportedAdoptionField:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.FAILED,
            outcome=AdoptionOutcome.FAILED,
            error_code="unsupported_field",
        )
    if target is None:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.STALE,
            outcome=AdoptionOutcome.TARGET_MISSING,
            error_code=AdoptionOutcome.TARGET_MISSING.value,
        )
    if not _candidate_integrity_valid(candidate):
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.STALE,
            outcome=AdoptionOutcome.STALE,
            error_code="candidate_integrity_failed",
        )

    validity_failure = _validity_failure(
        candidate=candidate,
        actor=actor,
        validity=candidate_validity(candidate),
    )
    if validity_failure is not None:
        return validity_failure
    if not spec.can_edit(actor, target):
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.FAILED,
            outcome=AdoptionOutcome.PERMISSION_DENIED,
            error_code=AdoptionOutcome.PERMISSION_DENIED.value,
        )

    current_value = canonicalize_text(getattr(target, candidate.target_field))
    target_updated_at_changed = target.updated_at != candidate.target_updated_at
    if canonical_text_hash(current_value) != candidate.previous_value_hash:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.CONFLICT,
            outcome=AdoptionOutcome.CONFLICT,
            error_code=AdoptionOutcome.CONFLICT.value,
            current_value=current_value,
            target_updated_at_changed=target_updated_at_changed,
        )

    requested_value = candidate.proposed_value if edited_value is None else edited_value
    if not isinstance(requested_value, str):
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.FAILED,
            outcome=AdoptionOutcome.VALIDATION_FAILED,
            error_code=AdoptionOutcome.VALIDATION_FAILED.value,
            current_value=current_value,
            edited_value=edited_value,
            target_updated_at_changed=target_updated_at_changed,
            errors={candidate.target_field: ["Der Übernahmewert muss Text sein."]},
        )

    final_value = canonicalize_text(requested_value)
    edited = edited_value is not None and final_value != candidate.proposed_value
    final_status = (
        FieldAdoptionCandidate.Status.ADOPTED_EDITED
        if edited
        else FieldAdoptionCandidate.Status.ADOPTED
    )
    final_outcome = AdoptionOutcome.ADOPTED_EDITED if edited else AdoptionOutcome.ADOPTED

    if canonical_text_hash(final_value) == canonical_text_hash(current_value):
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=final_status,
            outcome=final_outcome,
            current_value=current_value,
            final_value=current_value,
            edited_value=edited_value,
            target_updated_at_changed=target_updated_at_changed,
        )

    prepared = prepare_field_update(
        target_type=candidate.target_object_type,
        target=target,
        actor=actor,
        field_name=candidate.target_field,
        proposed_value=final_value,
    )
    if not prepared.is_valid:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.FAILED,
            outcome=AdoptionOutcome.VALIDATION_FAILED,
            error_code=AdoptionOutcome.VALIDATION_FAILED.value,
            current_value=current_value,
            edited_value=edited_value,
            target_updated_at_changed=target_updated_at_changed,
            errors=_form_errors(prepared.form),
        )

    apply_prepared_field_update(prepared=prepared, target=target)
    stored_value = canonicalize_text(getattr(target, candidate.target_field))
    return _complete_result(
        candidate=candidate,
        actor=actor,
        status=final_status,
        outcome=final_outcome,
        current_value=current_value,
        final_value=stored_value,
        edited_value=edited_value,
        target_updated_at_changed=target_updated_at_changed,
    )


@transaction.atomic
def reject_field_candidate(*, candidate_id, actor) -> AdoptionResult:
    _require_enabled()
    candidate, existing_result = _reserve_and_lock_candidate(
        candidate_id=candidate_id,
        actor=actor,
    )
    if existing_result is not None:
        return existing_result

    action = FieldAdoptionAudit.Action.REJECT
    try:
        spec, target = _lock_target(candidate)
    except UnsupportedAdoptionField:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.FAILED,
            outcome=AdoptionOutcome.FAILED,
            action=action,
            error_code="unsupported_field",
        )
    if target is None:
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.STALE,
            outcome=AdoptionOutcome.TARGET_MISSING,
            action=action,
            error_code=AdoptionOutcome.TARGET_MISSING.value,
        )
    if not _candidate_integrity_valid(candidate):
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.STALE,
            outcome=AdoptionOutcome.STALE,
            action=action,
            error_code="candidate_integrity_failed",
        )

    validity_failure = _validity_failure(
        candidate=candidate,
        actor=actor,
        validity=candidate_validity(candidate),
        action=action,
    )
    if validity_failure is not None:
        return validity_failure
    if not spec.can_edit(actor, target):
        return _complete_result(
            candidate=candidate,
            actor=actor,
            status=FieldAdoptionCandidate.Status.FAILED,
            outcome=AdoptionOutcome.PERMISSION_DENIED,
            action=action,
            error_code=AdoptionOutcome.PERMISSION_DENIED.value,
        )

    return _complete_result(
        candidate=candidate,
        actor=actor,
        status=FieldAdoptionCandidate.Status.REJECTED,
        outcome=AdoptionOutcome.REJECTED,
        action=action,
        current_value=canonicalize_text(getattr(target, candidate.target_field)),
    )
