from pathlib import Path


patch_path = Path("scripts/ap8_prepare.py")
patch_text = patch_path.read_text(encoding="utf-8")
patch_text = patch_text.replace(
    'help = "Lässt überfällige Capture-Entwürfe ablaufen und bereinigt terminale Sessions."',
    'help = "Lässt überfällige Capture-Entwürfe ablaufen und bereinigt alte Terminalzustände."',
    1,
)
old_query = '''def _expirable_sessions(*, checked_now):
    return CaptureSession.objects.filter(
        status__in=[CaptureSession.Status.DRAFT, CaptureSession.Status.COMPLETED],
        expires_at__lte=checked_now,
    ).exclude(analyses__status=CaptureAnalysis.Status.RUNNING)
'''
new_query = '''def _expirable_sessions(*, checked_now):
    running_session_ids = list(
        CaptureAnalysis.objects.filter(status=CaptureAnalysis.Status.RUNNING).values_list(
            "session_id", flat=True
        )
    )
    return CaptureSession.objects.filter(
        status__in=[CaptureSession.Status.DRAFT, CaptureSession.Status.COMPLETED],
        expires_at__lte=checked_now,
    ).exclude(pk__in=running_session_ids)
'''
if old_query not in patch_text:
    raise SystemExit("Expected retention query not found")
patch_path.write_text(patch_text.replace(old_query, new_query), encoding="utf-8")


test_path = Path("tests/test_capture_analysis_retention_privacy.py")
test_text = test_path.read_text(encoding="utf-8").replace("import logging\n", "")
test_text = test_text.replace(
    "def test_analysis_technical_log_contains_no_capture_or_suggestion_text(owner, caplog):\n",
    "def test_analysis_technical_log_contains_no_capture_or_suggestion_text(owner, monkeypatch):\n",
)
old_log_test = '''    caplog.set_level(logging.INFO, logger="ki_radar.accelerator.analysis_service")

    analysis_service.log_capture_analysis(analysis)

    assert "purpose=capture_extraction" in caplog.text
    assert "status=failed" in caplog.text
    assert "SENSIBEL" not in caplog.text
    assert "Beschaffung" not in caplog.text
'''
new_log_test = '''    logged = []

    def capture_log(message, *args):
        logged.append(message % args)

    monkeypatch.setattr(analysis_service.logger, "info", capture_log)
    analysis_service.log_capture_analysis(analysis)
    log_text = " ".join(logged)

    assert "purpose=capture_extraction" in log_text
    assert "status=failed" in log_text
    assert "SENSIBEL" not in log_text
    assert "Beschaffung" not in log_text
'''
if old_log_test not in test_text:
    raise SystemExit("Expected log test body not found")
test_path.write_text(test_text.replace(old_log_test, new_log_test), encoding="utf-8")
