from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from ki_radar.architecture.models import ProcessAnalysis
from ki_radar.core.llm_policy import (
    AcceleratorLLMPolicy,
    LLMConfigurationError,
    get_accelerator_llm_policy,
)

from .models import AcceleratorLLMQuota, SolutionGenerationRun
from .retention_policy import (
    CaptureRetentionConfigurationError,
    completed_capture_expiry,
)
from .solution_generation_contract import GENERATION_PROMPT_VERSION, GENERATION_SCHEMA_VERSION
from .solution_generation_sources import (
    SolutionGenerationReadinessError,
    SolutionGenerationSourceContext,
    require_solution_generation_ready,
)

logger = logging.getLogger(__name__)


class SolutionGenerationError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class SolutionGenerationAlreadyRunning(SolutionGenerationError):
    pass


class SolutionGenerationQuotaExceeded(SolutionGenerationError):
    pass


@dataclass(frozen=True)
class PreparedSolutionGeneration:
    run: SolutionGenerationRun
    source_context: SolutionGenerationSourceContext
    policy: AcceleratorLLMPolicy


def log_solution_generation_run(run: SolutionGenerationRun) -> None:
    logger.info(
        "llm_request purpose=solution_generation provider=%s model=%s "
        "object_type=process_analysis object_id=%s run_id=%s status=%s "
        "error_code=%s duration_ms=%s input_chars=%s output_chars=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s cost=%s",
        run.provider,
        run.model_name or "provider-default",
        run.process_analysis_id,
        run.pk,
        run.status,
        run.error_code or "none",
        run.duration_ms if run.duration_ms is not None else "",
        run.input_chars,
        run.output_chars,
        run.prompt_tokens if run.prompt_tokens is not None else "",
        run.completion_tokens if run.completion_tokens is not None else "",
        run.total_tokens if run.total_tokens is not None else "",
        run.cost if run.cost is not None else "",
    )


def _quota_subject(scope: str, *, actor, process_analysis: ProcessAnalysis) -> dict[str, object]:
    if scope == AcceleratorLLMQuota.Scope.CONTEXT:
        return {"process_analysis": process_analysis}
    if scope == AcceleratorLLMQuota.Scope.USER:
        return {"user": actor}
    return {}


def _increment_quota(
    *,
    scope: str,
    actor,
    process_analysis: ProcessAnalysis,
    quota_date,
    limit: int,
) -> None:
    subject = _quota_subject(scope, actor=actor, process_analysis=process_analysis)
    quota, _created = AcceleratorLLMQuota.objects.get_or_create(
        scope=scope,
        quota_date=quota_date,
        defaults={"calls": 0, **subject},
        **subject,
    )
    updated = AcceleratorLLMQuota.objects.filter(pk=quota.pk, calls__lt=limit).update(
        calls=F("calls") + 1
    )
    if updated:
        return

    labels = {
        AcceleratorLLMQuota.Scope.CONTEXT: "Diese Prozessanalyse",
        AcceleratorLLMQuota.Scope.USER: "Ihr Benutzerkonto",
        AcceleratorLLMQuota.Scope.GLOBAL: "Der Accelerator",
    }
    raise SolutionGenerationQuotaExceeded(
        f"{labels[scope]} hat das tägliche Generierungslimit erreicht.",
        code=f"{scope}_quota_exceeded",
    )


def _reserve_solution_generation_quotas(
    *,
    actor,
    process_analysis: ProcessAnalysis,
    policy: AcceleratorLLMPolicy,
    quota_date,
) -> None:
    for scope, limit in (
        (AcceleratorLLMQuota.Scope.CONTEXT, policy.max_calls_per_context),
        (AcceleratorLLMQuota.Scope.USER, policy.max_calls_per_user_day),
        (AcceleratorLLMQuota.Scope.GLOBAL, policy.max_calls_global_day),
    ):
        _increment_quota(
            scope=scope,
            actor=actor,
            process_analysis=process_analysis,
            quota_date=quota_date,
            limit=limit,
        )


def _duration_ms(run: SolutionGenerationRun, finished_at) -> int:
    return max(0, round((finished_at - run.started_at).total_seconds() * 1000))


@transaction.atomic
def prepare_solution_generation_run(*, actor, process_analysis_id) -> PreparedSolutionGeneration:
    process_analysis = (
        ProcessAnalysis.objects.select_for_update()
        .select_related("stage__value_stream")
        .prefetch_related("validations")
        .get(pk=process_analysis_id)
    )
    if SolutionGenerationRun.objects.filter(
        process_analysis=process_analysis,
        status=SolutionGenerationRun.Status.RUNNING,
    ).exists():
        raise SolutionGenerationAlreadyRunning(
            "Für diese Prozessanalyse läuft bereits eine Generierung.",
            code="generation_already_running",
        )

    try:
        source_context = require_solution_generation_ready(process_analysis)
    except SolutionGenerationReadinessError as exc:
        raise SolutionGenerationError(str(exc), code="process_not_ready") from exc

    try:
        policy = get_accelerator_llm_policy()
        expires_at = completed_capture_expiry()
    except (LLMConfigurationError, CaptureRetentionConfigurationError) as exc:
        raise SolutionGenerationError(
            f"Die Accelerator-Konfiguration ist ungültig: {exc}",
            code="invalid_configuration",
        ) from exc

    try:
        run = SolutionGenerationRun.objects.create(
            process_analysis=process_analysis,
            process_version=source_context.process_version,
            source_hash=source_context.source_hash,
            requested_by=actor,
            prompt_version=GENERATION_PROMPT_VERSION,
            generation_schema_version=GENERATION_SCHEMA_VERSION,
            expires_at=expires_at,
        )
    except IntegrityError as exc:
        raise SolutionGenerationAlreadyRunning(
            "Für diese Prozessanalyse läuft bereits eine Generierung.",
            code="generation_already_running",
        ) from exc

    _reserve_solution_generation_quotas(
        actor=actor,
        process_analysis=process_analysis,
        policy=policy,
        quota_date=timezone.localdate(),
    )
    return PreparedSolutionGeneration(
        run=run,
        source_context=source_context,
        policy=policy,
    )


@transaction.atomic
def mark_solution_generation_failed(*, run_id, error_code: str) -> SolutionGenerationRun:
    run = SolutionGenerationRun.objects.select_for_update().get(pk=run_id)
    if run.status != SolutionGenerationRun.Status.RUNNING:
        return run

    finished_at = timezone.now()
    run.status = SolutionGenerationRun.Status.FAILED
    run.finished_at = finished_at
    run.duration_ms = _duration_ms(run, finished_at)
    run.error_code = error_code
    run.save(
        update_fields=[
            "status",
            "finished_at",
            "duration_ms",
            "error_code",
            "updated_at",
        ]
    )
    log_solution_generation_run(run)
    return run
