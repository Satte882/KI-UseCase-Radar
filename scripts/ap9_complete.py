from pathlib import Path

contract_path = Path("ki_radar/accelerator/extraction_contract.py")
contract = contract_path.read_text(encoding="utf-8")
if "MAX_EXTRACTION_SUGGESTIONS = 100" not in contract:
    contract = contract.replace(
        'EXTRACTION_PROMPT_VERSION = "1.0"\n',
        'EXTRACTION_PROMPT_VERSION = "1.0"\nMAX_EXTRACTION_SUGGESTIONS = 100\n',
        1,
    )
old_loop = '''    suggestions: list[ExtractionSuggestion] = []
    for index, item in enumerate(_as_list(root.get("suggestions"), "suggestions", errors)):
'''
new_loop = '''    suggestions: list[ExtractionSuggestion] = []
    raw_suggestions = _as_list(root.get("suggestions"), "suggestions", errors)
    if len(raw_suggestions) > MAX_EXTRACTION_SUGGESTIONS:
        errors.append(
            "suggestions: Höchstens "
            f"{MAX_EXTRACTION_SUGGESTIONS} Vorschläge pro Analyse erlaubt."
        )
    for index, item in enumerate(raw_suggestions):
'''
if old_loop not in contract:
    raise SystemExit("Extraction suggestion loop anchor not found")
contract_path.write_text(contract.replace(old_loop, new_loop, 1), encoding="utf-8")

test_path = Path("tests/test_capture_analysis_golden.py")
test = test_path.read_text(encoding="utf-8")
if "from django.urls import reverse" not in test:
    test = test.replace(
        "from django.test import override_settings\n",
        "from django.test import override_settings\nfrom django.urls import reverse\n",
        1,
    )
if "    AcceleratorLLMQuota,\n" not in test:
    test = test.replace(
        "    CaptureAnalysis,\n    CaptureFieldSuggestion,\n",
        "    AcceleratorLLMQuota,\n    CaptureAnalysis,\n    CaptureFieldSuggestion,\n",
        1,
    )
test = test.replace(
    '@pytest.mark.parametrize("error_code", ["timeout", "provider_unavailable"])',
    '@pytest.mark.parametrize(\n'
    '    "error_code",\n'
    '    ["timeout", "provider_unavailable", "rate_limit", "response_too_large"],\n'
    ')',
    1,
)
marker = "def test_real_demo_enforces_context_user_and_global_quota("
if marker not in test:
    test += r'''

@pytest.mark.django_db
@pytest.mark.parametrize(
    ("scope", "setting_name", "error_code"),
    [
        ("context", "ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT", "context_quota_exceeded"),
        ("user", "ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY", "user_quota_exceeded"),
        ("global", "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY", "global_quota_exceeded"),
    ],
)
def test_real_demo_enforces_context_user_and_global_quota(
    owner,
    scope,
    setting_name,
    error_code,
):
    session = _completed_session(owner, _case("value_stream"))
    subject = {}
    if scope == AcceleratorLLMQuota.Scope.CONTEXT:
        subject["session"] = session
    elif scope == AcceleratorLLMQuota.Scope.USER:
        subject["user"] = owner
    AcceleratorLLMQuota.objects.create(
        scope=scope,
        quota_date=timezone.localdate(),
        calls=1,
        **subject,
    )
    configured = {**LIMITS}
    configured["ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT"] = "1"
    if scope in {AcceleratorLLMQuota.Scope.USER, AcceleratorLLMQuota.Scope.GLOBAL}:
        configured["ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY"] = "1"
    if scope == AcceleratorLLMQuota.Scope.GLOBAL:
        configured["ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY"] = "1"

    with override_settings(**configured), pytest.raises(
        analysis_service.CaptureAnalysisQuotaExceeded
    ) as exc_info:
        analysis_service.prepare_capture_analysis(actor=owner, session_id=session.pk)

    assert exc_info.value.code == error_code
    assert CaptureAnalysis.objects.count() == 0


@pytest.mark.django_db
@override_settings(
    **{
        **LIMITS,
        "ACCELERATOR_LLM_MAX_CALLS_PER_CONTEXT": "1",
        "ACCELERATOR_LLM_MAX_CALLS_PER_USER_DAY": "1",
        "ACCELERATOR_LLM_MAX_CALLS_GLOBAL_DAY": "1",
    }
)
def test_real_demo_daily_quotas_reset_on_new_local_date(owner):
    session = _completed_session(owner, _case("value_stream"))
    yesterday = timezone.localdate() - timedelta(days=1)
    AcceleratorLLMQuota.objects.create(
        scope=AcceleratorLLMQuota.Scope.CONTEXT,
        quota_date=yesterday,
        session=session,
        calls=1,
    )
    AcceleratorLLMQuota.objects.create(
        scope=AcceleratorLLMQuota.Scope.USER,
        quota_date=yesterday,
        user=owner,
        calls=1,
    )
    AcceleratorLLMQuota.objects.create(
        scope=AcceleratorLLMQuota.Scope.GLOBAL,
        quota_date=yesterday,
        calls=1,
    )

    analysis_service.prepare_capture_analysis(actor=owner, session_id=session.pk)

    today_quotas = AcceleratorLLMQuota.objects.filter(quota_date=timezone.localdate())
    assert {quota.scope: quota.calls for quota in today_quotas} == {
        AcceleratorLLMQuota.Scope.CONTEXT: 1,
        AcceleratorLLMQuota.Scope.USER: 1,
        AcceleratorLLMQuota.Scope.GLOBAL: 1,
    }


@pytest.mark.django_db
@override_settings(**LIMITS)
def test_real_demo_result_redisplay_is_idempotent_without_provider_call(
    owner,
    client,
    monkeypatch,
):
    case = _case("value_stream")
    session = _completed_session(owner, case)
    calls = 0

    def provider(**kwargs):
        nonlocal calls
        calls += 1
        return _provider_result(case["provider_payload"])

    monkeypatch.setattr(analysis_service, "request_openrouter", provider)
    analysis = execute_capture_analysis(actor=owner, session_id=session.pk)
    client.force_login(owner)

    for _index in range(2):
        response = client.get(
            reverse("accelerator:analysis_detail", kwargs={"analysis_id": analysis.pk})
        )
        assert response.status_code == 200

    assert calls == 1
    assert CaptureAnalysis.objects.filter(pk=analysis.pk).count() == 1


@pytest.mark.django_db
@override_settings(**LIMITS)
def test_real_demo_rejects_excessive_suggestion_count_atomically(owner, monkeypatch):
    case = _case("value_stream")
    session = _completed_session(owner, case)
    payload = copy.deepcopy(case["provider_payload"])
    base = payload["suggestions"][0]
    payload["suggestions"] = [
        {
            **base,
            "target_field": "value_stream.stages[].name",
            "target_object_type": "value_stream_stage",
            "target_group_key": f"phase-{index}",
            "source_question": "vs_stages",
            "source_excerpt": "LIEFERE",
            "suggested_value": f"Phase {index}",
        }
        for index in range(101)
    ]
    monkeypatch.setattr(
        analysis_service,
        "request_openrouter",
        lambda **kwargs: _provider_result(payload),
    )

    with pytest.raises(analysis_service.CaptureAnalysisError) as exc_info:
        execute_capture_analysis(actor=owner, session_id=session.pk)

    analysis = CaptureAnalysis.objects.get(session=session)
    assert exc_info.value.code == "invalid_extraction"
    assert analysis.status == CaptureAnalysis.Status.FAILED
    assert analysis.suggestions.count() == 0
'''
test_path.write_text(test, encoding="utf-8")
