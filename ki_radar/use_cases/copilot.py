from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict

from django.conf import settings

from ki_radar.core.llm_policy import LLMConfigurationError, get_accelerator_llm_policy

from .models import UseCase
from .services import current_decision_check

logger = logging.getLogger(__name__)


class CopilotUnavailable(RuntimeError):
    def __init__(self, message: str, *, code: str = "unavailable") -> None:
        super().__init__(message)
        self.code = code


def _setting(name: str, default: str = "") -> str:
    return str(getattr(settings, name, os.getenv(name, default)) or "")


def _payload_for_use_case(use_case: UseCase) -> dict:
    decision = current_decision_check(use_case)
    return {
        "id": use_case.short_id,
        "title": use_case.title,
        "status": use_case.get_status_display(),
        "problem": use_case.problem_statement,
        "expected_benefit": use_case.expected_benefit,
        "primary_metric": {
            "name": use_case.metric_name,
            "type": use_case.get_metric_type_display() if use_case.metric_type else "",
            "direction": (
                use_case.get_metric_direction_display() if use_case.metric_direction else ""
            ),
            "unit": use_case.metric_unit,
            "baseline": (
                str(use_case.metric_baseline) if use_case.metric_baseline is not None else ""
            ),
            "target": str(use_case.metric_target) if use_case.metric_target is not None else "",
            "actual": str(use_case.metric_actual) if use_case.metric_actual is not None else "",
            "method": use_case.metric_measurement_method,
            "period": use_case.metric_measurement_period,
        },
        "legacy_success_criterion": use_case.success_criterion,
        "legacy_result": use_case.realized_result,
        "costs": {
            "one_time": str(use_case.one_time_cost or ""),
            "recurring": str(use_case.recurring_cost or ""),
        },
        "deterministic_check": asdict(decision),
    }


def _usage_metadata(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return {}
    allowed = (
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cost",
    )
    return {name: usage.get(name) for name in allowed if usage.get(name) is not None}


def _log_request(
    *,
    use_case: UseCase,
    model: str,
    status: str,
    error_code: str,
    started_at: float,
    input_chars: int,
    output_chars: int,
    usage: dict[str, object],
) -> None:
    logger.info(
        "llm_request purpose=use_case_review provider=openrouter model=%s "
        "object_type=use_case object_id=%s status=%s error_code=%s "
        "duration_ms=%s input_chars=%s output_chars=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s cost=%s",
        model or "provider-default",
        getattr(use_case, "pk", ""),
        status,
        error_code or "none",
        round((time.monotonic() - started_at) * 1000),
        input_chars,
        output_chars,
        usage.get("prompt_tokens", ""),
        usage.get("completion_tokens", ""),
        usage.get("total_tokens", ""),
        usage.get("cost", ""),
    )


def analyze_use_case(use_case: UseCase) -> str:
    started_at = time.monotonic()
    status = "failed"
    error_code = "unexpected"
    input_chars = 0
    output_chars = 0
    usage: dict[str, object] = {}
    model = _setting("OPENROUTER_MODEL")

    try:
        api_key = _setting("OPENROUTER_API_KEY")
        if not api_key:
            error_code = "not_configured"
            raise CopilotUnavailable(
                "Kein OpenRouter API-Key konfiguriert.",
                code=error_code,
            )

        try:
            policy = get_accelerator_llm_policy()
        except LLMConfigurationError as exc:
            error_code = "invalid_configuration"
            raise CopilotUnavailable(
                f"Die LLM-Konfiguration ist ungültig: {exc}",
                code=error_code,
            ) from exc

        system_prompt = (
            "Du bist ein kritischer Review-Copilot für KI-Piloten in deutschen KMU. "
            "Du triffst keine Freigabeentscheidung und ersetzt keine Rechts-, Datenschutz- oder "
            "Security-Prüfung. Prüfe ausschließlich die semantische Konsistenz zwischen Problem, "
            "erwartetem Nutzen, primärer Erfolgsmetrik, Ziel, gemessenem Ergebnis, Kosten und der "
            "anstehenden Entscheidung. Antworte auf Deutsch, kompakt und ohne erfundene Fakten. "
            "Nutze genau die Überschriften 'Konsistenz', 'Auffälligkeiten', 'Rückfragen' und "
            "'Entscheidungshinweis'. Kennzeichne Unsicherheit ausdrücklich."
        )
        user_content = json.dumps(_payload_for_use_case(use_case), ensure_ascii=False)
        input_chars = len(system_prompt) + len(user_content)
        if input_chars > policy.max_input_chars:
            error_code = "input_too_large"
            raise CopilotUnavailable(
                "Die für die Analyse vorgesehenen Eingaben überschreiten das konfigurierte "
                "Größenlimit.",
                code=error_code,
            )

        body = {
            "temperature": 0.1,
            "max_tokens": policy.max_output_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if model:
            body["model"] = model

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": _setting("OPENROUTER_APP_NAME", "KI-Radar"),
        }
        site_url = _setting("OPENROUTER_SITE_URL")
        if site_url:
            headers["HTTP-Referer"] = site_url

        api_url = _setting(
            "OPENROUTER_API_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        parsed_url = urllib.parse.urlparse(api_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            error_code = "invalid_configuration"
            raise CopilotUnavailable(
                "Die OpenRouter API-URL muss eine gültige HTTPS-URL sein.",
                code=error_code,
            )

        request = urllib.request.Request(  # noqa: S310
            api_url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(  # nosec B310  # noqa: S310
                request,
                timeout=policy.timeout_seconds,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                error_code = "rate_limit"
                message = "OpenRouter hat das Aufruflimit erreicht. Bitte später erneut versuchen."
            elif exc.code in {401, 403}:
                error_code = "unauthorized"
                message = "OpenRouter ist nicht korrekt autorisiert."
            elif 500 <= exc.code <= 599:
                error_code = "provider_unavailable"
                message = "OpenRouter ist derzeit nicht verfügbar."
            else:
                error_code = "provider_error"
                message = "Die OpenRouter-Anfrage wurde abgelehnt."
            raise CopilotUnavailable(message, code=error_code) from exc
        except TimeoutError as exc:
            error_code = "timeout"
            raise CopilotUnavailable(
                "Die OpenRouter-Anfrage hat das Zeitlimit überschritten.",
                code=error_code,
            ) from exc
        except urllib.error.URLError as exc:
            error_code = "provider_unavailable"
            raise CopilotUnavailable(
                "OpenRouter ist derzeit nicht erreichbar.",
                code=error_code,
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            error_code = "invalid_response"
            raise CopilotUnavailable(
                "OpenRouter hat ein ungültiges Antwortformat zurückgegeben.",
                code=error_code,
            ) from exc

        usage = _usage_metadata(payload)
        try:
            content = payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            error_code = "invalid_response"
            raise CopilotUnavailable(
                "OpenRouter hat ein unerwartetes Antwortformat zurückgegeben.",
                code=error_code,
            ) from exc
        if not content:
            error_code = "empty_response"
            raise CopilotUnavailable(
                "OpenRouter hat keine Analyse zurückgegeben.",
                code=error_code,
            )
        output_chars = len(content)
        status = "success"
        error_code = ""
        return content
    finally:
        _log_request(
            use_case=use_case,
            model=model,
            status=status,
            error_code=error_code,
            started_at=started_at,
            input_chars=input_chars,
            output_chars=output_chars,
            usage=usage,
        )
