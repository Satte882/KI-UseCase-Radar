from pathlib import Path


def replace(path_name, old, new):
    path = Path(path_name)
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path_name}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace(
    "config/settings/base.py",
    'ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY = env(\n    "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY",\n    "100",\n)\n',
    'ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY = env(\n    "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY",\n    "100",\n)\nACCELERATOR_CAPTURE_COMPLETED_RETENTION_DAYS = env(\n    "ACCELERATOR_CAPTURE_COMPLETED_RETENTION_DAYS",\n    "90",\n)\n',
)
replace(
    ".env.example",
    "# Die persistente Zählung der Request-Grenzen folgt mit dem Capture-/Vorschlagskontext.\n",
    "# Request-Grenzen werden im Capture-/Vorschlagskontext persistent gezählt.\n",
)
replace(
    ".env.example",
    "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY=100\n",
    "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY=100\n\n"
    "# Aufbewahrung abgeschlossener Capture Sessions und ihrer Analysen.\n"
    "# Zulässig sind 30 bis 365 Tage; Standard für die Block-5-Übergangsphase: 90 Tage.\n"
    "ACCELERATOR_CAPTURE_COMPLETED_RETENTION_DAYS=90\n",
)
replace(
    "ki_radar/accelerator/services.py",
    "from .retention import expire_capture_session_if_due\n",
    "from .retention import expire_capture_session_if_due\n"
    "from .retention_policy import completed_capture_expiry\n",
)
replace(
    "ki_radar/accelerator/services.py",
    "    session.status = CaptureSession.Status.COMPLETED\n"
    "    session.completed_at = now\n"
    "    session.revision += 1\n",
    "    session.status = CaptureSession.Status.COMPLETED\n"
    "    session.completed_at = now\n"
    "    session.expires_at = completed_capture_expiry(now=now)\n"
    "    session.revision += 1\n",
)
replace(
    "ki_radar/accelerator/services.py",
    '            "completed_at",\n            "revision",\n',
    '            "completed_at",\n            "expires_at",\n            "revision",\n',
)

Path("ki_radar/accelerator/retention.py").write_text(
    '''from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import CaptureAnalysis, CaptureSession

CAPTURE_PURGE_GRACE_DAYS = 7


def _expirable_sessions(*, checked_now):
    return CaptureSession.objects.filter(
        status__in=[CaptureSession.Status.DRAFT, CaptureSession.Status.COMPLETED],
        expires_at__lte=checked_now,
    ).exclude(analyses__status=CaptureAnalysis.Status.RUNNING)


def expire_due_capture_sessions(*, now=None, owner=None) -> int:
    """Move overdue editable or completed captures to the terminal expired state."""
    checked_now = now or timezone.now()
    sessions = _expirable_sessions(checked_now=checked_now)
    if owner is not None:
        sessions = sessions.filter(owner=owner)
    return sessions.update(
        status=CaptureSession.Status.EXPIRED,
        expired_at=checked_now,
        updated_at=checked_now,
    )


def expire_capture_session_if_due(session: CaptureSession, *, now=None) -> CaptureSession:
    checked_now = now or timezone.now()
    expirable_states = {CaptureSession.Status.DRAFT, CaptureSession.Status.COMPLETED}
    if session.status not in expirable_states or session.expires_at > checked_now:
        return session
    if session.analyses.filter(status=CaptureAnalysis.Status.RUNNING).exists():
        return session

    updated = _expirable_sessions(checked_now=checked_now).filter(pk=session.pk).update(
        status=CaptureSession.Status.EXPIRED,
        expired_at=checked_now,
        updated_at=checked_now,
    )
    if updated:
        session.status = CaptureSession.Status.EXPIRED
        session.expired_at = checked_now
        session.updated_at = checked_now
    else:
        session.refresh_from_db()
    return session


def purge_terminal_capture_sessions(
    *,
    now=None,
    grace_days: int = CAPTURE_PURGE_GRACE_DAYS,
) -> int:
    """Physically remove expired or discarded sessions after the grace period."""
    if grace_days < 0:
        raise ValueError("Die Karenzzeit darf nicht negativ sein.")

    checked_now = now or timezone.now()
    cutoff = checked_now - timedelta(days=grace_days)
    sessions = CaptureSession.objects.filter(
        Q(
            status=CaptureSession.Status.EXPIRED,
            expired_at__isnull=False,
            expired_at__lte=cutoff,
        )
        | Q(
            status=CaptureSession.Status.DISCARDED,
            discarded_at__isnull=False,
            discarded_at__lte=cutoff,
        )
    )
    deleted_count = sessions.count()
    sessions.delete()
    return deleted_count
''',
    encoding="utf-8",
)

path = Path("ki_radar/accelerator/analysis_service.py")
text = path.read_text(encoding="utf-8")
text = text.replace("import json\n", "import json\nimport logging\n")
text = text.replace(
    "from django.utils import timezone\n",
    "from django.utils import timezone\n"
    "from django.views.decorators.debug import sensitive_variables\n",
)
text = text.replace(
    "from .models import AcceleratorLLMQuota, CaptureAnalysis, CaptureSession\n",
    "from .models import AcceleratorLLMQuota, CaptureAnalysis, CaptureSession\n"
    "from .retention_policy import (\n"
    "    CaptureRetentionConfigurationError,\n"
    "    completed_capture_expiry,\n"
    ")\n",
)
text = text.replace(
    "EXTRACTION_SYSTEM_PROMPT = (\n",
    "logger = logging.getLogger(__name__)\n\n\nEXTRACTION_SYSTEM_PROMPT = (\n",
)
marker = "def canonical_answer_hash(answers: dict[str, str]) -> str:\n"
log_function = '''def log_capture_analysis(analysis: CaptureAnalysis) -> None:
    logger.info(
        "llm_request purpose=capture_extraction provider=%s model=%s "
        "object_type=capture_session object_id=%s analysis_id=%s status=%s "
        "error_code=%s duration_ms=%s input_chars=%s output_chars=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s cost=%s",
        analysis.provider,
        analysis.model_name or "provider-default",
        analysis.session_id,
        analysis.pk,
        analysis.status,
        analysis.error_code or "none",
        analysis.duration_ms if analysis.duration_ms is not None else "",
        analysis.input_chars,
        analysis.output_chars,
        analysis.prompt_tokens if analysis.prompt_tokens is not None else "",
        analysis.completion_tokens if analysis.completion_tokens is not None else "",
        analysis.total_tokens if analysis.total_tokens is not None else "",
        analysis.cost if analysis.cost is not None else "",
    )


'''
if marker not in text:
    raise SystemExit("analysis_service marker missing")
text = text.replace(marker, log_function + marker)
text = text.replace(
    "@transaction.atomic\ndef prepare_capture_analysis",
    '@sensitive_variables("answers", "input_document", "user_content", "messages")\n'
    "@transaction.atomic\ndef prepare_capture_analysis",
)
text = text.replace(
    "    try:\n"
    "        policy = get_accelerator_llm_policy()\n"
    "    except LLMConfigurationError as exc:\n",
    "    try:\n"
    "        policy = get_accelerator_llm_policy()\n"
    "        completed_expiry = completed_capture_expiry()\n"
    "    except (LLMConfigurationError, CaptureRetentionConfigurationError) as exc:\n",
)
old = '''    return PreparedCaptureAnalysis(
        analysis=analysis,
        catalog=catalog,
        answers=answers,
        messages=messages,
        policy=policy,
    )
'''
new = '''    session.expires_at = completed_expiry
    session.save(update_fields=["expires_at", "updated_at"])
    return PreparedCaptureAnalysis(
        analysis=analysis,
        catalog=catalog,
        answers=answers,
        messages=messages,
        policy=policy,
    )
'''
if old not in text:
    raise SystemExit("prepare return block missing")
text = text.replace(old, new)
old = '''    )
    return analysis


def request_capture_provider'''
new = '''    )
    log_capture_analysis(analysis)
    return analysis


@sensitive_variables("prepared", "result", "payload")
def request_capture_provider'''
if old not in text:
    raise SystemExit("failed analysis return block missing")
text = text.replace(old, new)
path.write_text(text, encoding="utf-8")

path = Path("ki_radar/accelerator/extraction_validation.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "    mark_capture_analysis_failed,\n",
    "    log_capture_analysis,\n    mark_capture_analysis_failed,\n",
)
old = '''    )
    return analysis


def execute_capture_analysis'''
new = '''    )
    log_capture_analysis(analysis)
    return analysis


def execute_capture_analysis'''
if old not in text:
    raise SystemExit("successful analysis return block missing")
path.write_text(text.replace(old, new), encoding="utf-8")

replace(
    "ki_radar/accelerator/management/commands/purge_capture_sessions.py",
    'help = "Lässt überfällige Capture-Entwürfe ablaufen und bereinigt terminale Sessions."',
    'help = "Lässt überfällige Capture Sessions ablaufen und bereinigt terminale Sessions."',
)
