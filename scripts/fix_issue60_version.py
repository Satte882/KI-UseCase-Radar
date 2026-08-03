from pathlib import Path

path = Path("ki_radar/architecture/models.py")
text = path.read_text(encoding="utf-8")

wrong = (
    '    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)\n'
    '    version = models.PositiveIntegerField(default=1, editable=False)\n'
)
correct = '    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)\n'
if wrong not in text:
    raise RuntimeError("Incorrect ValueStream version placement not found")
text = text.replace(wrong, correct, 1)

anchor = (
    '    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)\n'
    '    scope_start = models.TextField(verbose_name="Prozessstart")\n'
)
replacement = (
    '    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)\n'
    '    version = models.PositiveIntegerField(default=1, editable=False)\n'
    '    scope_start = models.TextField(verbose_name="Prozessstart")\n'
)
if anchor not in text:
    raise RuntimeError("ProcessAnalysis version insertion point not found")
path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
