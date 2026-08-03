from pathlib import Path

path = Path("tests/test_guided_workflow_ux.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from ki_radar.delivery.actions import build_actionable_findings, primary_delivery_action\n",
    "from ki_radar.delivery.actions import primary_delivery_action\n",
    1,
)
path.write_text(text, encoding="utf-8")

Path("scripts/fix_issue37_test_import.py").unlink()
workflow = Path(".github/workflows/fix-issue37-test-import.yml")
if workflow.exists():
    workflow.unlink()
