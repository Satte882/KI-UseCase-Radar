from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict

from django.conf import settings

from .models import UseCase
from .services import current_decision_check


class CopilotUnavailable(RuntimeError):
    pass


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


def analyze_use_case(use_case: UseCase) -> str:
    api_key = _setting("OPENROUTER_API_KEY")
    if not api_key:
        raise CopilotUnavailable("Kein OpenRouter API-Key konfiguriert.")

    system_prompt = (
        "Du bist ein kritischer Review-Copilot für KI-Piloten in deutschen KMU. "
        "Du triffst keine Freigabeentscheidung und ersetzt keine Rechts-, Datenschutz- oder "
        "Security-Prüfung. Prüfe ausschließlich die semantische Konsistenz zwischen Problem, "
        "erwartetem Nutzen, primärer Erfolgsmetrik, Ziel, gemessenem Ergebnis, Kosten und der "
        "anstehenden Entscheidung. Antworte auf Deutsch, kompakt und ohne erfundene Fakten. "
        "Nutze genau die Überschriften 'Konsistenz', 'Auffälligkeiten', 'Rückfragen' und "
        "'Entscheidungshinweis'. Kennzeichne Unsicherheit ausdrücklich."
    )
    body = {
        "temperature": 0.1,
        "max_tokens": 700,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(_payload_for_use_case(use_case), ensure_ascii=False),
            },
        ],
    }
    model = _setting("OPENROUTER_MODEL")
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

    request = urllib.request.Request(
        _setting(
            "OPENROUTER_API_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        ),
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        timeout = int(_setting("OPENROUTER_TIMEOUT_SECONDS", "30"))
        with urllib.request.urlopen(  # nosec B310  # noqa: S310
            request, timeout=timeout
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error_payload = json.loads(exc.read().decode("utf-8"))
            message = error_payload.get("error", {}).get("message", str(exc))
        except (json.JSONDecodeError, AttributeError):
            message = str(exc)
        raise CopilotUnavailable(f"OpenRouter-Anfrage fehlgeschlagen: {message}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise CopilotUnavailable("OpenRouter ist derzeit nicht erreichbar.") from exc

    try:
        content = payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError) as exc:
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = error.get("message", "Unerwartete Antwort von OpenRouter.")
        raise CopilotUnavailable(str(message)) from exc
    if not content:
        raise CopilotUnavailable("OpenRouter hat keine Analyse zurückgegeben.")
    return content
