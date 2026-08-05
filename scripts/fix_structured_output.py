from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Anchor not found in {path}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: str, marker: str, content: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if marker in text:
        return
    file_path.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")


replace_once(
    "ki_radar/core/openrouter.py",
    '''@dataclass(frozen=True)\nclass OpenRouterResult:\n    content: str\n    model: str\n    usage: dict[str, object]\n    output_chars: int\n''',
    '''@dataclass(frozen=True)\nclass OpenRouterResult:\n    content: str\n    model: str\n    usage: dict[str, object]\n    output_chars: int\n    finish_reason: str = ""\n''',
)

replace_once(
    "ki_radar/core/openrouter.py",
    '''def _usage_metadata(payload: object) -> dict[str, object]:\n    if not isinstance(payload, dict):\n        return {}\n    usage = payload.get("usage")\n    if not isinstance(usage, dict):\n        return {}\n    allowed = ("prompt_tokens", "completion_tokens", "total_tokens", "cost")\n    return {name: usage.get(name) for name in allowed if usage.get(name) is not None}\n\n\ndef _api_url() -> str:\n''',
    '''def _usage_metadata(payload: object) -> dict[str, object]:\n    if not isinstance(payload, dict):\n        return {}\n    usage = payload.get("usage")\n    if not isinstance(usage, dict):\n        return {}\n    allowed = ("prompt_tokens", "completion_tokens", "total_tokens", "cost")\n    return {name: usage.get(name) for name in allowed if usage.get(name) is not None}\n\n\ndef _http_error_payload(exc: urllib.error.HTTPError) -> dict[str, Any]:\n    try:\n        raw = exc.read(MAX_OPENROUTER_RESPONSE_BYTES + 1)\n    except (AttributeError, OSError):\n        return {}\n    if not raw or len(raw) > MAX_OPENROUTER_RESPONSE_BYTES:\n        return {}\n    try:\n        payload = json.loads(raw.decode("utf-8"))\n    except (UnicodeDecodeError, json.JSONDecodeError):\n        return {}\n    return payload if isinstance(payload, dict) else {}\n\n\ndef _requires_json_schema(\n    response_format: dict[str, Any] | None,\n    provider: dict[str, Any] | None,\n) -> bool:\n    return bool(\n        response_format\n        and response_format.get("type") == "json_schema"\n        and provider\n        and provider.get("require_parameters") is True\n    )\n\n\ndef _schema_provider_unavailable(payload: dict[str, Any]) -> bool:\n    error = payload.get("error")\n    if not isinstance(error, dict):\n        return False\n    message = str(error.get("message") or "").casefold()\n    metadata = error.get("metadata")\n    error_type = ""\n    if isinstance(metadata, dict):\n        error_type = str(metadata.get("error_type") or "").casefold()\n    markers = (\n        "routing requirements",\n        "requested parameters",\n        "support the requested parameters",\n        "structured output",\n        "json schema",\n        "no endpoints found",\n    )\n    return error_type in {"no_available_provider", "provider_routing_error"} or any(\n        marker in message for marker in markers\n    )\n\n\ndef _api_url() -> str:\n''',
)

replace_once(
    "ki_radar/core/openrouter.py",
    '''def request_openrouter(\n    *,\n    messages: list[dict[str, str]],\n    max_tokens: int,\n    timeout_seconds: int,\n    temperature: float = 0.1,\n    response_format: dict[str, Any] | None = None,\n) -> OpenRouterResult:\n''',
    '''def request_openrouter(\n    *,\n    messages: list[dict[str, str]],\n    max_tokens: int,\n    timeout_seconds: int,\n    temperature: float = 0.1,\n    response_format: dict[str, Any] | None = None,\n    provider: dict[str, Any] | None = None,\n) -> OpenRouterResult:\n''',
)

replace_once(
    "ki_radar/core/openrouter.py",
    '''    if response_format is not None:\n        body["response_format"] = response_format\n\n    request = urllib.request.Request(  # noqa: S310\n''',
    '''    if response_format is not None:\n        body["response_format"] = response_format\n    if provider is not None:\n        body["provider"] = provider\n\n    request = urllib.request.Request(  # noqa: S310\n''',
)

replace_once(
    "ki_radar/core/openrouter.py",
    '''    except urllib.error.HTTPError as exc:\n        if exc.code == 429:\n            code = "rate_limit"\n            message = "OpenRouter hat das Aufruflimit erreicht. Bitte später erneut versuchen."\n        elif exc.code in {401, 403}:\n            code = "unauthorized"\n            message = "OpenRouter ist nicht korrekt autorisiert."\n        elif 500 <= exc.code <= 599:\n            code = "provider_unavailable"\n            message = "OpenRouter ist derzeit nicht verfügbar."\n        else:\n            code = "provider_error"\n            message = "Die OpenRouter-Anfrage wurde abgelehnt."\n        raise OpenRouterUnavailable(message, code=code) from exc\n''',
    '''    except urllib.error.HTTPError as exc:\n        error_payload = _http_error_payload(exc)\n        if exc.code == 429:\n            code = "rate_limit"\n            message = "OpenRouter hat das Aufruflimit erreicht. Bitte später erneut versuchen."\n        elif exc.code in {401, 403}:\n            code = "unauthorized"\n            message = "OpenRouter ist nicht korrekt autorisiert."\n        elif (\n            exc.code == 503\n            and _requires_json_schema(response_format, provider)\n            and _schema_provider_unavailable(error_payload)\n        ):\n            code = "provider_schema_unsupported"\n            message = (\n                "Für das konfigurierte Modell steht kein OpenRouter-Provider bereit, "\n                "der das erforderliche strukturierte Ausgabeschema unterstützt."\n            )\n        elif 500 <= exc.code <= 599:\n            code = "provider_unavailable"\n            message = "OpenRouter ist derzeit nicht verfügbar."\n        else:\n            code = "provider_error"\n            message = "Die OpenRouter-Anfrage wurde abgelehnt."\n        raise OpenRouterUnavailable(message, code=code) from exc\n''',
)

replace_once(
    "ki_radar/core/openrouter.py",
    '''    usage = _usage_metadata(payload)\n    try:\n        content = payload["choices"][0]["message"]["content"].strip()\n    except (KeyError, IndexError, TypeError, AttributeError) as exc:\n        raise OpenRouterUnavailable(\n            "OpenRouter hat ein unerwartetes Antwortformat zurückgegeben.",\n            code="invalid_response",\n        ) from exc\n''',
    '''    usage = _usage_metadata(payload)\n    try:\n        choice = payload["choices"][0]\n        content = choice["message"]["content"].strip()\n        finish_reason = str(choice.get("finish_reason") or "")\n    except (KeyError, IndexError, TypeError, AttributeError) as exc:\n        raise OpenRouterUnavailable(\n            "OpenRouter hat ein unerwartetes Antwortformat zurückgegeben.",\n            code="invalid_response",\n        ) from exc\n''',
)

replace_once(
    "ki_radar/core/openrouter.py",
    '''    return OpenRouterResult(\n        content=content,\n        model=str(returned_model or model),\n        usage=usage,\n        output_chars=len(content),\n    )\n''',
    '''    return OpenRouterResult(\n        content=content,\n        model=str(returned_model or model),\n        usage=usage,\n        output_chars=len(content),\n        finish_reason=finish_reason,\n    )\n''',
)

replace_once(
    "ki_radar/accelerator/extraction_contract.py",
    '''def target_object_type_for_path(path: str) -> str:\n    prefixes = (\n        ("value_stream.stages[].", "value_stream_stage"),\n        ("solution_options[].", "solution_option"),\n        ("value_stream.", "value_stream"),\n        ("process_analysis.", "process_analysis"),\n        ("use_case.", "use_case"),\n    )\n    for prefix, object_type in prefixes:\n        if path.startswith(prefix):\n            return object_type\n    raise ValueError(f"Unbekannter Accelerator-Zielpfad: {path}")\n\n\ndef _exact_fields(\n''',
    '''def target_object_type_for_path(path: str) -> str:\n    prefixes = (\n        ("value_stream.stages[].", "value_stream_stage"),\n        ("solution_options[].", "solution_option"),\n        ("value_stream.", "value_stream"),\n        ("process_analysis.", "process_analysis"),\n        ("use_case.", "use_case"),\n    )\n    for prefix, object_type in prefixes:\n        if path.startswith(prefix):\n            return object_type\n    raise ValueError(f"Unbekannter Accelerator-Zielpfad: {path}")\n\n\ndef build_extraction_json_schema(catalog: CaptureCatalog) -> dict[str, Any]:\n    """Build the provider schema from the frozen server-side contract."""\n\n    target_paths = sorted(allowed_extraction_target_paths(catalog))\n    question_keys = sorted(catalog.question_map)\n    target_object_types = sorted(\n        {target_object_type_for_path(path) for path in target_paths}\n    )\n    finding_schema = {\n        "type": "object",\n        "additionalProperties": False,\n        "required": ["message", "source_questions"],\n        "properties": {\n            "message": {\n                "type": "string",\n                "minLength": 1,\n                "description": "Konkrete offene Frage oder festgestellter Widerspruch.",\n            },\n            "source_questions": {\n                "type": "array",\n                "items": {"type": "string", "enum": question_keys},\n                "description": "Betroffene Fragen aus dem eingefrorenen Katalog.",\n            },\n        },\n    }\n    suggestion_schema = {\n        "type": "object",\n        "additionalProperties": False,\n        "required": [\n            "target_object_type",\n            "target_field",\n            "target_group_key",\n            "field_type",\n            "suggested_value",\n            "source_question",\n            "source_excerpt",\n            "uncertainty",\n            "uncertainty_reason",\n        ],\n        "properties": {\n            "target_object_type": {\n                "type": "string",\n                "enum": target_object_types,\n                "description": "Aus dem Zielpfad abgeleiteter Objekt-Typ.",\n            },\n            "target_field": {\n                "type": "string",\n                "enum": target_paths,\n                "description": "Zulässiger Zielpfad aus dem eingefrorenen Katalog.",\n            },\n            "target_group_key": {\n                "anyOf": [\n                    {\n                        "type": "string",\n                        "minLength": 1,\n                        "pattern": GROUP_KEY_PATTERN.pattern,\n                    },\n                    {"type": "null"},\n                ],\n                "description": "Lokaler Gruppenschlüssel für wiederholbare Ziele, sonst null.",\n            },\n            "field_type": {\n                "type": "string",\n                "enum": sorted(ALLOWED_FIELD_TYPES),\n            },\n            "suggested_value": {\n                "anyOf": [\n                    {"type": "string", "minLength": 1},\n                    {"type": "integer"},\n                    {"type": "boolean"},\n                    {\n                        "type": "array",\n                        "minItems": 1,\n                        "items": {"type": "string", "minLength": 1},\n                    },\n                ],\n                "description": "Typisierter Vorschlagswert; Dezimalwerte bleiben Strings.",\n            },\n            "source_question": {\n                "type": "string",\n                "enum": question_keys,\n            },\n            "source_excerpt": {\n                "type": "string",\n                "minLength": 1,\n                "description": "Wörtlicher Ausschnitt aus der Nutzerantwort.",\n            },\n            "uncertainty": {\n                "type": "string",\n                "enum": sorted(ALLOWED_UNCERTAINTY_LEVELS),\n            },\n            "uncertainty_reason": {"type": "string", "minLength": 1},\n        },\n    }\n    return {\n        "$schema": "https://json-schema.org/draft/2020-12/schema",\n        "type": "object",\n        "additionalProperties": False,\n        "required": [\n            "schema_version",\n            "prompt_version",\n            "suggestions",\n            "open_questions",\n            "contradictions",\n        ],\n        "properties": {\n            "schema_version": {\n                "type": "string",\n                "const": EXTRACTION_SCHEMA_VERSION,\n            },\n            "prompt_version": {\n                "type": "string",\n                "const": EXTRACTION_PROMPT_VERSION,\n            },\n            "suggestions": {\n                "type": "array",\n                "maxItems": MAX_EXTRACTION_SUGGESTIONS,\n                "items": suggestion_schema,\n            },\n            "open_questions": {"type": "array", "items": finding_schema},\n            "contradictions": {"type": "array", "items": finding_schema},\n        },\n    }\n\n\ndef _exact_fields(\n''',
)

replace_once(
    "ki_radar/accelerator/analysis_service.py",
    '''from .extraction_contract import EXTRACTION_PROMPT_VERSION, EXTRACTION_SCHEMA_VERSION\n''',
    '''from .extraction_contract import (\n    EXTRACTION_PROMPT_VERSION,\n    EXTRACTION_SCHEMA_VERSION,\n    build_extraction_json_schema,\n)\n''',
)

replace_once(
    "ki_radar/accelerator/analysis_service.py",
    '''@sensitive_variables("prepared", "result", "payload")\ndef request_capture_provider(prepared: PreparedCaptureAnalysis) -> CaptureProviderPayload:\n    try:\n        result = request_openrouter(\n            messages=prepared.messages,\n            max_tokens=prepared.policy.max_output_tokens,\n            timeout_seconds=prepared.policy.timeout_seconds,\n            temperature=0.0,\n            response_format={"type": "json_object"},\n        )\n    except OpenRouterUnavailable as exc:\n        mark_capture_analysis_failed(analysis_id=prepared.analysis.pk, error_code=exc.code)\n        raise CaptureAnalysisError(str(exc), code=exc.code) from exc\n\n    try:\n''',
    '''@sensitive_variables("prepared", "result", "payload", "response_schema")\ndef request_capture_provider(prepared: PreparedCaptureAnalysis) -> CaptureProviderPayload:\n    response_schema = build_extraction_json_schema(prepared.catalog)\n    try:\n        result = request_openrouter(\n            messages=prepared.messages,\n            max_tokens=prepared.policy.max_output_tokens,\n            timeout_seconds=prepared.policy.timeout_seconds,\n            temperature=0.0,\n            response_format={\n                "type": "json_schema",\n                "json_schema": {\n                    "name": "accelerator_capture_extraction_v1",\n                    "strict": True,\n                    "schema": response_schema,\n                },\n            },\n            provider={"require_parameters": True},\n        )\n    except OpenRouterUnavailable as exc:\n        mark_capture_analysis_failed(analysis_id=prepared.analysis.pk, error_code=exc.code)\n        raise CaptureAnalysisError(str(exc), code=exc.code) from exc\n\n    if result.finish_reason == "length":\n        mark_capture_analysis_failed(\n            analysis_id=prepared.analysis.pk,\n            error_code="output_truncated",\n            result=result,\n        )\n        raise CaptureAnalysisError(\n            "Die Providerantwort wurde am konfigurierten Ausgabelimit abgeschnitten.",\n            code="output_truncated",\n        )\n\n    try:\n''',
)

replace_once(
    "config/settings/base.py",
    '''ACCELERATOR_LLM_TIMEOUT_SECONDS = env(\n    "ACCELERATOR_LLM_TIMEOUT_SECONDS",\n    OPENROUTER_TIMEOUT_SECONDS,\n)\nACCELERATOR_LLM_MAX_INPUT_CHARS = env("ACCELERATOR_LLM_MAX_INPUT_CHARS", "12000")\nACCELERATOR_LLM_MAX_OUTPUT_TOKENS = env("ACCELERATOR_LLM_MAX_OUTPUT_TOKENS", "700")\n''',
    '''ACCELERATOR_LLM_TIMEOUT_SECONDS = env(\n    "ACCELERATOR_LLM_TIMEOUT_SECONDS",\n    "60",\n)\nACCELERATOR_LLM_MAX_INPUT_CHARS = env("ACCELERATOR_LLM_MAX_INPUT_CHARS", "12000")\nACCELERATOR_LLM_MAX_OUTPUT_TOKENS = env("ACCELERATOR_LLM_MAX_OUTPUT_TOKENS", "4096")\n''',
)

replace_once(
    ".env.example",
    '''ACCELERATOR_LLM_TIMEOUT_SECONDS=30\nACCELERATOR_LLM_MAX_INPUT_CHARS=12000\nACCELERATOR_LLM_MAX_OUTPUT_TOKENS=700\n''',
    '''ACCELERATOR_LLM_TIMEOUT_SECONDS=60\nACCELERATOR_LLM_MAX_INPUT_CHARS=12000\nACCELERATOR_LLM_MAX_OUTPUT_TOKENS=4096\n''',
)

replace_once(
    "tests/test_extraction_contract.py",
    '''    allowed_extraction_target_paths,\n    parse_extraction_document,\n''',
    '''    allowed_extraction_target_paths,\n    build_extraction_json_schema,\n    parse_extraction_document,\n''',
)

append_once(
    "tests/test_extraction_contract.py",
    "def test_provider_schema_is_derived_from_frozen_catalog():",
    '''def test_provider_schema_is_derived_from_frozen_catalog():\n    catalog = get_capture_catalog("value_stream", "1.0")\n\n    schema = build_extraction_json_schema(catalog)\n    suggestion_schema = schema["properties"]["suggestions"]["items"]\n\n    assert schema["additionalProperties"] is False\n    assert schema["properties"]["schema_version"]["const"] == EXTRACTION_SCHEMA_VERSION\n    assert schema["properties"]["prompt_version"]["const"] == EXTRACTION_PROMPT_VERSION\n    assert set(suggestion_schema["properties"]["target_field"]["enum"]) == set(\n        allowed_extraction_target_paths(catalog)\n    )\n    assert "use_case.title" not in suggestion_schema["properties"]["target_field"]["enum"]\n    assert set(suggestion_schema["properties"]["source_question"]["enum"]) == set(\n        catalog.question_map\n    )\n    assert suggestion_schema["additionalProperties"] is False\n''',
)

replace_once(
    "tests/test_accelerator_llm.py",
    '''import json\nimport logging\n''',
    '''import io\nimport json\nimport logging\n''',
)

replace_once(
    "tests/test_accelerator_llm.py",
    '''    assert captured["body"]["max_tokens"] == 400\n    assert captured["body"]["model"] == "test/model"\n''',
    '''    assert captured["body"]["max_tokens"] == 400\n    assert captured["body"]["model"] == "test/model"\n    assert "provider" not in captured["body"]\n    assert "response_format" not in captured["body"]\n''',
)

append_once(
    "tests/test_accelerator_llm.py",
    "def test_transport_forwards_structured_output_requirements_and_finish_reason",
    '''@override_settings(\n    OPENROUTER_API_KEY="test-key",\n    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",\n    **VALID_LIMITS,\n)\ndef test_transport_forwards_structured_output_requirements_and_finish_reason(monkeypatch):\n    captured = {}\n    payload = _success_payload('{"schema_version":"1.0"}')\n    payload["choices"][0]["finish_reason"] = "stop"\n\n    def fake_urlopen(request, timeout):\n        captured["body"] = json.loads(request.data.decode("utf-8"))\n        return FakeResponse(payload)\n\n    monkeypatch.setattr(openrouter.urllib.request, "urlopen", fake_urlopen)\n\n    result = openrouter.request_openrouter(\n        messages=[{"role": "user", "content": "test"}],\n        max_tokens=100,\n        timeout_seconds=5,\n        response_format={\n            "type": "json_schema",\n            "json_schema": {"name": "test", "strict": True, "schema": {"type": "object"}},\n        },\n        provider={"require_parameters": True},\n    )\n\n    assert captured["body"]["provider"] == {"require_parameters": True}\n    assert captured["body"]["response_format"]["type"] == "json_schema"\n    assert result.finish_reason == "stop"\n\n\n@override_settings(\n    OPENROUTER_API_KEY="test-key",\n    OPENROUTER_API_URL="https://openrouter.example/v1/chat/completions",\n    **VALID_LIMITS,\n)\ndef test_transport_classifies_missing_schema_provider(monkeypatch):\n    error_payload = {\n        "error": {\n            "code": 503,\n            "message": "No endpoints found that support the requested parameters.",\n            "metadata": {"error_type": "no_available_provider"},\n        }\n    }\n    http_error = openrouter.urllib.error.HTTPError(\n        "https://openrouter.example/v1/chat/completions",\n        503,\n        "Service Unavailable",\n        {},\n        io.BytesIO(json.dumps(error_payload).encode("utf-8")),\n    )\n\n    def raise_schema_error(*args, **kwargs):\n        raise http_error\n\n    monkeypatch.setattr(openrouter.urllib.request, "urlopen", raise_schema_error)\n\n    with pytest.raises(openrouter.OpenRouterUnavailable) as exc_info:\n        openrouter.request_openrouter(\n            messages=[{"role": "user", "content": "test"}],\n            max_tokens=100,\n            timeout_seconds=5,\n            response_format={\n                "type": "json_schema",\n                "json_schema": {\n                    "name": "test",\n                    "strict": True,\n                    "schema": {"type": "object"},\n                },\n            },\n            provider={"require_parameters": True},\n        )\n\n    assert exc_info.value.code == "provider_schema_unsupported"\n''',
)

replace_once(
    "tests/test_capture_analysis_service.py",
    '''    monkeypatch.setattr(\n        analysis_service,\n        "request_openrouter",\n        lambda **kwargs: OpenRouterResult(\n            content=json.dumps(response),\n            model="test/model",\n            usage={"total_tokens": 12, "cost": 0.001},\n            output_chars=100,\n        ),\n    )\n\n    provider = analysis_service.request_capture_provider(prepared)\n\n    assert provider.payload == response\n    assert provider.result.model == "test/model"\n    assert prepared.analysis.status == CaptureAnalysis.Status.RUNNING\n''',
    '''    captured = {}\n\n    def fake_request_openrouter(**kwargs):\n        captured.update(kwargs)\n        return OpenRouterResult(\n            content=json.dumps(response),\n            model="test/model",\n            usage={"total_tokens": 12, "cost": 0.001},\n            output_chars=100,\n            finish_reason="stop",\n        )\n\n    monkeypatch.setattr(analysis_service, "request_openrouter", fake_request_openrouter)\n\n    provider = analysis_service.request_capture_provider(prepared)\n\n    assert provider.payload == response\n    assert provider.result.model == "test/model"\n    assert captured["provider"] == {"require_parameters": True}\n    assert captured["response_format"]["type"] == "json_schema"\n    assert captured["response_format"]["json_schema"]["strict"] is True\n    assert (\n        captured["response_format"]["json_schema"]["schema"]["properties"][\n            "schema_version"\n        ]["const"]\n        == "1.0"\n    )\n    assert prepared.analysis.status == CaptureAnalysis.Status.RUNNING\n''',
)

append_once(
    "tests/test_capture_analysis_service.py",
    "def test_truncated_provider_output_has_explicit_error_code",
    '''@pytest.mark.django_db\n@override_settings(**LIMITS)\ndef test_truncated_provider_output_has_explicit_error_code(owner, monkeypatch):\n    session = _completed_session(owner)\n    prepared = analysis_service.prepare_capture_analysis(actor=owner, session_id=session.pk)\n    monkeypatch.setattr(\n        analysis_service,\n        "request_openrouter",\n        lambda **kwargs: OpenRouterResult(\n            content='{"schema_version":"1.0"',\n            model="test/model",\n            usage={"completion_tokens": 700},\n            output_chars=23,\n            finish_reason="length",\n        ),\n    )\n\n    with pytest.raises(analysis_service.CaptureAnalysisError) as exc_info:\n        analysis_service.request_capture_provider(prepared)\n\n    prepared.analysis.refresh_from_db()\n    assert exc_info.value.code == "output_truncated"\n    assert prepared.analysis.error_code == "output_truncated"\n    assert prepared.analysis.status == CaptureAnalysis.Status.FAILED\n    assert prepared.analysis.completion_tokens == 700\n\n\n@pytest.mark.django_db\n@override_settings(**LIMITS)\ndef test_schema_provider_error_is_preserved_on_analysis(owner, monkeypatch):\n    session = _completed_session(owner)\n    prepared = analysis_service.prepare_capture_analysis(actor=owner, session_id=session.pk)\n\n    def fail_provider(**kwargs):\n        raise OpenRouterUnavailable(\n            "Kein kompatibler Provider",\n            code="provider_schema_unsupported",\n        )\n\n    monkeypatch.setattr(analysis_service, "request_openrouter", fail_provider)\n\n    with pytest.raises(analysis_service.CaptureAnalysisError) as exc_info:\n        analysis_service.request_capture_provider(prepared)\n\n    prepared.analysis.refresh_from_db()\n    assert exc_info.value.code == "provider_schema_unsupported"\n    assert prepared.analysis.error_code == "provider_schema_unsupported"\n    assert prepared.analysis.status == CaptureAnalysis.Status.FAILED\n''',
)

append_once(
    "docs/accelerator/BLOCK_4_COMPLETION.md",
    "## Nachtrag: Reale Structured-Output-Integration",
    '''## Nachtrag: Reale Structured-Output-Integration\n\nNach dem formalen Block-4-Abschluss zeigte ein realer OpenRouter-Aufruf eine Integrationslücke, die von den vollständig simulierten Providerantworten der ursprünglichen Regression nicht erkannt wurde. Die Nachverfolgung erfolgt transparent in Issue #163 und einem separaten Fix-PR.\n\nDer Nachtrag korrigiert keine fachliche Scope-Entscheidung aus Block 4, sondern den realen Providervertrag:\n\n- das Ausgabelimit wird von 700 auf 4096 Tokens angehoben und der Timeout auf 60 Sekunden gesetzt,\n- der vorhandene versionierte Extraktionsvertrag wird als striktes JSON Schema an OpenRouter übermittelt,\n- `provider.require_parameters=true` schließt Provider aus, die das Schema ignorieren würden,\n- abgeschnittene Antworten werden als `output_truncated` statt als generisches `invalid_response` protokolliert,\n- ein fehlender kompatibler Schema-Provider wird als `provider_schema_unsupported` ausgewiesen,\n- die bestehende atomare serverseitige Validierung bleibt als zweite, maßgebliche Schutzschicht unverändert bestehen.\n\nDie Ergänzung wird durch Transport-, Vertrags- und Analyse-Service-Regressionen abgesichert. Issue #120 bleibt als historischer Blockabschluss geschlossen; dieser Nachtrag stellt den später erkannten Realbetrieb-Fix nachvollziehbar daneben.\n''',
)
