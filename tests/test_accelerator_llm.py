import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.test import override_settings

from ki_radar.core.llm_policy import LLMConfigurationError, get_accelerator_llm_policy
from ki_radar.use_cases import copilot

VALID_LIMITS = {
    "ACCELERATOR_LLM_TIMEOUT_SECONDS": "15",
    "ACCELERATOR_LLM_MAX_INPUT_CHARS": "5000",
    "ACCELERATOR_LLM_MAX_OUTPUT_TOKENS": "400",
    "ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT": "3",
    "ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY": "20",
    "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY": "100",
}


class FakeResponse:
    def __init__(self, payload: object):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


def _use_case():
    return SimpleNamespace(pk="use-case-1")


def _success_payload(content: str = "Konsistenz\nPlausibel") -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
            "cost": 0.001,
        },
    }


@override_settings(**VALID_LIMITS)
def test_policy_parses_valid_settings():
    policy = get_accelerator_llm_policy()

    assert policy.timeout_seconds == 15
    assert policy.max_input_chars == 5000
    assert policy.max_output_tokens == 400
    assert policy.max_calls_per_context == 3


@pytest.mark.parametrize(
    ("setting", "value", "message"),
    [
        ("ACCELERATOR_LLM_TIMEOUT_SECONDS", "nicht-numerisch", "ganze Zahl"),
        ("ACCELERATOR_LLM_MAX_INPUT_CHARS", "0", "zwischen"),
        ("ACCELERATOR_LLM_MAX_OUTPUT_TOKENS", "5000", "zwischen"),
    ],
)
def test_policy_rejects_invalid_numeric_settings(setting, value, message):
    configured = {**VALID_LIMITS, setting: value}

    with override_settings(**configured), pytest.raises(LLMConfigurationError, match=message):
        get_accelerator_llm_policy()


def test_policy_rejects_inconsistent_request_limits():
    configured = {
        **VALID_LIMITS,
        "ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT": "21",
        "ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY": "20",
    }

    with override_settings(**configured), pytest.raises(
        LLMConfigurationError,
        match="nutzerbezogene Tagesgrenze",
    ):
        get_accelerator_llm_policy()


@override_settings(OPENROUTER_API_KEY="", **VALID_LIMITS)
def test_copilot_requires_api_key(monkeypatch):
    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"secret": "unused"})

    with pytest.raises(copilot.CopilotUnavailable) as exc_info:
        copilot.analyze_use_case(_use_case())

    assert exc_info.value.code == "not_configured"


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    **{**VALID_LIMITS, "ACCELERATOR_LLM_MAX_INPUT_CHARS": "10"},
)
def test_copilot_rejects_oversized_input_without_network_call(monkeypatch):
    calls = 0

    def fake_urlopen(*args, **kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse(_success_payload())

    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"text": "vertraulich"})
    monkeypatch.setattr(copilot.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(copilot.CopilotUnavailable) as exc_info:
        copilot.analyze_use_case(_use_case())

    assert exc_info.value.code == "input_too_large"
    assert calls == 0


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    OPENROUTER_MODEL="test/model",
    **VALID_LIMITS,
)
def test_copilot_uses_shared_timeout_and_output_limit(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(_success_payload())

    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"problem": "klar"})
    monkeypatch.setattr(copilot.urllib.request, "urlopen", fake_urlopen)

    result = copilot.analyze_use_case(_use_case())

    assert result == "Konsistenz\nPlausibel"
    assert captured["timeout"] == 15
    assert captured["body"]["max_tokens"] == 400
    assert captured["body"]["model"] == "test/model"


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    **VALID_LIMITS,
)
def test_copilot_classifies_rate_limit(monkeypatch):
    http_error = copilot.urllib.error.HTTPError(
        "https://openrouter.example/v1/chat/completions",
        429,
        "Too Many Requests",
        {},
        None,
    )

    def raise_rate_limit(*args, **kwargs):
        raise http_error

    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"problem": "klar"})
    monkeypatch.setattr(copilot.urllib.request, "urlopen", raise_rate_limit)

    with pytest.raises(copilot.CopilotUnavailable) as exc_info:
        copilot.analyze_use_case(_use_case())

    assert exc_info.value.code == "rate_limit"


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    **VALID_LIMITS,
)
def test_copilot_does_not_retry_after_timeout(monkeypatch):
    calls = 0

    def fake_urlopen(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise TimeoutError

    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"problem": "klar"})
    monkeypatch.setattr(copilot.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(copilot.CopilotUnavailable) as exc_info:
        copilot.analyze_use_case(_use_case())

    assert exc_info.value.code == "timeout"
    assert calls == 1


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    **VALID_LIMITS,
)
def test_copilot_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"problem": "klar"})
    monkeypatch.setattr(
        copilot.urllib.request,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(b"{"),
    )

    with pytest.raises(copilot.CopilotUnavailable) as exc_info:
        copilot.analyze_use_case(_use_case())

    assert exc_info.value.code == "invalid_response"


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    **VALID_LIMITS,
)
def test_copilot_rejects_empty_response(monkeypatch):
    monkeypatch.setattr(copilot, "_payload_for_use_case", lambda use_case: {"problem": "klar"})
    monkeypatch.setattr(
        copilot.urllib.request,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(_success_payload("   ")),
    )

    with pytest.raises(copilot.CopilotUnavailable) as exc_info:
        copilot.analyze_use_case(_use_case())

    assert exc_info.value.code == "empty_response"


@override_settings(
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",
    **VALID_LIMITS,
)
def test_copilot_logs_metadata_without_prompt_or_raw_content(monkeypatch, caplog):
    sensitive_content = "SEHR-VERTRAULICHER-INHALT"
    monkeypatch.setattr(
        copilot,
        "_payload_for_use_case",
        lambda use_case: {"problem": sensitive_content},
    )
    monkeypatch.setattr(
        copilot.urllib.request,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(_success_payload("Antwort ohne Rohdaten")),
    )
    caplog.set_level(logging.INFO, logger="ki_radar.use_cases.copilot")

    copilot.analyze_use_case(_use_case())

    log_text = caplog.text
    assert "status=success" in log_text
    assert "total_tokens=30" in log_text
    assert sensitive_content not in log_text
    assert "Antwort ohne Rohdaten" not in log_text


def test_copilot_submit_guard_is_loaded_and_prevents_second_submit():
    repository_root = Path(__file__).resolve().parents[1]
    base_template = (repository_root / "templates" / "base.html").read_text(encoding="utf-8")
    guard_script = (repository_root / "static" / "js" / "copilot-submit-guard.js").read_text(
        encoding="utf-8"
    )

    assert "js/copilot-submit-guard.js" in base_template
    assert 'form[action$="/copilot/"]' in guard_script
    assert 'form.dataset.submitted === "true"' in guard_script
    assert 'button.setAttribute("aria-busy", "true")' in guard_script
    assert "Analyse läuft …" in guard_script
