from pathlib import Path


path = Path("ki_radar/use_cases/decision_views.py")
text = path.read_text(encoding="utf-8")
old = 'f"an {decision.second_approval_assignee.get_display_name()} zugewiesen.",'
new = (
    'f"an {decision.second_approval_assignee.get_display_name()} "\n'
    '                            "zugewiesen.",'
)
if old not in text:
    raise RuntimeError("Generated assignment message not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

path = Path("tests/test_guided_second_approval.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from django.contrib.auth.models import Group\n",
    "from django.contrib.auth.models import Group\n"
    "from django.core.exceptions import PermissionDenied\n",
    1,
)
text = text.replace(
    "from ki_radar.use_cases.models import ApprovalDecision, DecisionAssessment, UseCase\n",
    "from ki_radar.use_cases.models import DecisionAssessment, UseCase\n",
    1,
)
text = text.replace(
    "with pytest.raises(Exception):",
    "with pytest.raises(PermissionDenied):",
    1,
)
path.write_text(text, encoding="utf-8")

old_migration = Path("ki_radar/use_cases/migrations/0003_guided_second_approval.py")
new_migration = Path("ki_radar/use_cases/migrations/0006_guided_second_approval.py")
migration_text = old_migration.read_text(encoding="utf-8")
migration_text = migration_text.replace(
    '("use_cases", "0002_decision_quality_metrics")',
    '("use_cases", "0005_use_case_classification")',
    1,
)
new_migration.write_text(migration_text, encoding="utf-8")
old_migration.unlink()
