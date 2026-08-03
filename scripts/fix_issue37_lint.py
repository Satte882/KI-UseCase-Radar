from pathlib import Path

path = Path("ki_radar/delivery/actions.py")
text = path.read_text(encoding="utf-8")
text = text.replace("from ki_radar.use_cases.models import UseCase\n", "", 1)
path.write_text(text, encoding="utf-8")

Path("scripts/fix_issue37_lint.py").unlink()
workflow = Path(".github/workflows/fix-issue37-lint.yml")
if workflow.exists():
    workflow.unlink()
