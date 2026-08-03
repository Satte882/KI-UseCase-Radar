from pathlib import Path

path = Path("ki_radar/architecture/forms.py")
text = path.read_text(encoding="utf-8")
old = (
    '            "Die Rolle ist von Business Owner und Technical Owner eines späteren '
    'Use Cases getrennt."\n'
)
new = (
    '            "Die Rolle ist von Business Owner und Technical Owner "\n'
    '            "eines späteren Use Cases getrennt."\n'
)
if old not in text:
    raise RuntimeError("Expected generated help-text line not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
